# Changelog

## [5.0.0]
- **[BREAKING]** [ENH] Renamed the arguments of `optionfactory.services.bundle` and `optionfactory.services.service`: `service_name` -> `name`, `service_image` -> `image`, `service_template` -> `template`, `service_args` -> `opts` + `args`.
- **[BREAKING]** [ENH] The image is no longer passed inside the arguments string: it must be specified via the new mandatory `image` argument, which is also prefetched and injected into the template context.
- **[BREAKING]** [ENH] `image` is now mandatory in `optionfactory.services.bundle` and `optionfactory.services.service`.
- [ENH] Split the former `service_args` into `opts` (container/service options) and `args` (command arguments), rendered by the bundled templates as `{{ opts }} {{ image }} {{ args }}`.
- [ENH] Updated the bundled `docker_service.j2`, `podman_service.j2` and `network_service.j2` templates to the new context variables (`name`, `image`, `opts`, `args`).
- [ENH] Updated documentation and molecule tests to the new argument names.

## [4.1.0]
- Added the `service_image` argument used to prefetch docker images in `optionfactory.services.bundle` and `optionfactory.services.service` plugins.

## [4.0.1]
### Added
- WireGuard mesh VPN support.
