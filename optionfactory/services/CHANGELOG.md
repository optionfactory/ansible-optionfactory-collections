# Changelog

## [5.0.0]
- **[BREAKING]** [NEW] Added engine blocks to `optionfactory.services.bundle` and `optionfactory.services.service`: exactly one of `container` or `command` is required, replacing the former flat arguments (`service_name` -> `name`; `service_image`/`service_args` -> the `image`/`opts`/`args` block options).
- [NEW] The `container` block selects the engine via `engine` (`docker` (default) or `podman`) and supports `image` (mandatory, prefetched and injected into the template context), `opts`, `args`, `env` (a `KEY: value` mapping, rendered as `--env`), `network`, `ip` (rendered as `--network`/`--ip`), `publish` (rendered as `-p`, empty entries skipped), `mounts` (rendered as `--mount type=bind,...`, each supports a `when` conditional) and `volumes` (rendered as `--volume`).
- **[BREAKING]** [ENH] The image is no longer part of the options string: it must be specified via `image`.
- **[BREAKING]** [ENH] Replaced the bundled `network_service.j2` template with `command_service.j2`: plain services use the `command` block with `exec` (mandatory) and `args`.
- [ENH] Per-engine template defaults: `docker_service.j2`, `podman_service.j2`, `command_service.j2`.
- [ENH] Updated documentation and molecule tests.
- **[BREAKING]** [ENH] `optionfactory.services.docker` now configures the official Docker repository automatically when `package` is `docker-ce`; the bundled `docker_repository` role has been removed.

## [4.1.0]
- Added the `service_image` argument used to prefetch docker images in `optionfactory.services.bundle` and `optionfactory.services.service` plugins.

## [4.0.1]
### Added
- WireGuard mesh VPN support.
