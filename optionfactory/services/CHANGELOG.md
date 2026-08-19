# Changelog

## [5.0.0]
- [ENH] Rewrote the `optionfactory.services.ps1` prompt: 24-bit true color, hostname color cached per shell, git branch as `[branch]` with dimmed brackets (single fork, detached-HEAD fallback to short commit id), docker indicator via `/.dockerenv`/`/run/.containerenv` (cgroup v2 safe), ✔/✘ status icons, `\001`/`\002` readline markers. Removed Mercurial support.
- [NEW] Added `optionfactory.services.timer`: provisions a oneshot systemd service and its timer in one step. Engine blocks (`container` with `engine`/`container`/`exec`/`args`/`opts`, or `command` with `exec`/`args`), scheduling via `on_boot_sec`/`on_unit_active_sec`/`on_calendar` (at least one required), plus `persistent`, `accuracy_sec`, `randomized_delay_sec`, `unit` and custom `template`/`timer_template`.
- **[BREAKING]** [REM] Removed `optionfactory.services.legopfa`: superseded by `optionfactory.services.timer`, which produces equivalent units. Migration:
  ```yml
  # before
  - optionfactory.services.legopfa:
      container_name: my-lego-container

  # after
  - optionfactory.services.timer:
      name: legopfa-renewal
      container:
        container: my-lego-container
        exec: /legopfa-all
      on_boot_sec: 15min
      on_unit_active_sec: 1w
  ```
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
