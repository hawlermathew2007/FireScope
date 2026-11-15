import gc
import logging
import pandas as pd
import pyarrow.dataset as ds
from shapely import wkb
from pathlib import Path

from .io import iter_csv_chunks
from .geometry import add_approximate_footprints
from ..core.preprocessing import normalize, prescreen

logger = logging.getLogger(__name__)


def load_parquet_directory(
    directory: Path,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:

    directory = Path(directory)

    files = sorted(directory.glob("*.parquet"))

    if not files:
        return pd.DataFrame()

    dataset = ds.dataset(
        [str(path) for path in files],
        format="parquet",
    )

    filter_expression = None

    if start_date is not None:
        start_date = pd.Timestamp(
            start_date
        ).strftime("%Y-%m-%d")

        filter_expression = (
            ds.field("acq_date") >= start_date
        )

    if end_date is not None:
        end_date = pd.Timestamp(
            end_date
        ).strftime("%Y-%m-%d")

        end_filter = (
            ds.field("acq_date") <= end_date
        )

        filter_expression = (
            end_filter
            if filter_expression is None
            else filter_expression & end_filter
        )

    scanner = dataset.scanner(
        filter=filter_expression,
        batch_size=50_000,
        use_threads=True,
    )

    frames = []

    for record_batch in scanner.to_batches():
        frame = record_batch.to_pandas()

        if not frame.empty:
            frames.append(frame)

        del frame, record_batch

    if not frames:
        return pd.DataFrame()

    data = pd.concat(
        frames,
        ignore_index=True,
        copy=False,
    )

    del frames
    gc.collect()

    # Reconstruct geometries only after filtering by date.
    if "geometry_wkb" in data.columns:

        data["geometry"] = data["geometry_wkb"].map(
            lambda value: (
                wkb.loads(value)
                if value is not None
                else None
            )
        )

        data.drop(
            columns=["geometry_wkb"],
            inplace=True,
        )

    gc.collect()

    return data


def process_files_to_parquet(
    input_files,
    output_dir,
    sensor: str,
    vegetation_only: bool = True,
    chunksize: int = 100_000,
    force_reprocess: bool = False,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_read = 0
    total_kept = 0
    total_files_skipped = 0
    total_files_processed = 0

    for input_file in input_files:
        input_file = Path(input_file)

        # One final Parquet file per input CSV
        output_path = output_dir / (
            f"{sensor.lower()}_{input_file.stem}.parquet"
        )

        temp_path = output_dir / (
            f"{sensor.lower()}_{input_file.stem}.tmp.parquet"
        )

        done_path = output_dir / (
            f"{sensor.lower()}_{input_file.stem}.done"
        )

        # Skip files already processed
        if output_path.exists() and not force_reprocess:
            logger.info(f"[{sensor}] Skipping existing: {output_path.name}")
            total_files_skipped += 1
            continue

        # Remove incomplete temporary output from previous failed runs
        if temp_path.exists():
            temp_path.unlink()

        logger.info(f"[{sensor}] Processing: {input_file.name}")

        file_read = 0
        file_kept = 0
        writer = None

        try:
            for chunk in iter_csv_chunks(
                [input_file],
                sensor=sensor,
                chunksize=chunksize,
            ):
                file_read += len(chunk)

                normalized = normalize(chunk, sensor)

                screened = prescreen(
                    normalized,
                    vegetation_only=vegetation_only,
                )

                if not screened.empty:
                    screened = add_approximate_footprints(screened)

                    # Convert geometry to WKB for Parquet storage
                    screened["geometry_wkb"] = screened["geometry"].map(
                        lambda geom: geom.wkb if geom is not None else None
                    )

                    screened = screened.drop(columns=["geometry"])

                    # Write chunks incrementally using PyArrow
                    import pyarrow as pa
                    import pyarrow.parquet as pq

                    table = pa.Table.from_pandas(
                        screened,
                        preserve_index=False,
                    )

                    if writer is None:
                        writer = pq.ParquetWriter(
                            temp_path,
                            table.schema,
                            compression="snappy",
                        )

                    writer.write_table(table)
                    file_kept += len(screened)

                del chunk, normalized, screened
                gc.collect()

            if writer is not None:
                writer.close()
                writer = None

                temp_path.replace(output_path)

                if done_path.exists():
                    done_path.unlink()

            else:
                logger.info(
                    f"[{sensor}] No records retained from {input_file.name}"
                )

                # Mark the empty input as successfully processed.
                done_path.touch()

            total_read += file_read
            total_kept += file_kept
            total_files_processed += 1

            logger.info(
                f"[{sensor}] Completed {input_file.name}: "
                f"{file_read:,} read, {file_kept:,} retained."
            )

        except Exception:
            if writer is not None:
                writer.close()

            logger.exception(
                f"[{sensor}] Failed processing {input_file.name}"
            )
            raise

    logger.info(
        f"[{sensor}] Finished preprocessing. "
        f"Read {total_read:,} rows; retained {total_kept:,} rows. "
        f"Processed {total_files_processed} files; "
        f"skipped {total_files_skipped} existing files."
    )

    return output_dir
