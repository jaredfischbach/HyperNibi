# Changelog

## 0.1.1

- Route CPU tasks automatically to large-memory workers when requested memory is at least 96000 MiB and at least CPUs × 16 × 1024 MiB; route all other CPU tasks to base workers.
- Use `worker/cpu=1` for both CPU worker families while keeping scheduling separate, including on connected workers with spare capacity, to prevent cross-family backfilling.
- Allow either CPU or memory utilization to satisfy the 50% allocation minimum.
- Add large-memory worker options at 1/8, 1/16, and 1/32, all with a 50% allocation minimum.
- Add a base 1/32 worker option with a 0% allocation minimum and set the base 1/16 option to 50%.
- Update documentation with worker sizing tables, automatic routing rules, numeric fractions, and Nextflow settings for large-memory tasks.
- Add regression coverage for routing boundaries, allocation thresholds, worker sizing, and connected-worker scheduling.

## 0.1.0

- Initial release.
