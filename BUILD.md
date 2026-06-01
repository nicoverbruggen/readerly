# Building Readerly

## Building with the `fntbld` container (any platform)

The easiest, most reproducible way to build Readerly on any platform is to use the prebuilt `fntbld` container image. The container already includes all prerequisites, so there's nothing to install beyond a container runtime ([Docker](https://www.docker.com/) or [Podman](https://podman.io/)). This is the same image used by the CI pipeline.

From the root of the repository, mount the current directory into the container and run the build:

```bash
docker run --rm -v "$PWD":/work -w /work \
  ghcr.io/nicoverbruggen/fntbld-oci:latest \
  python3 build.py
```

With Podman, substitute `podman` for `docker` — the arguments are identical:

```bash
podman run --rm -v "$PWD":/work -w /work \
  ghcr.io/nicoverbruggen/fntbld-oci:latest \
  python3 build.py
```

The generated fonts appear in `out/ttf`, `out/kf`, and `out/web` on your host, just as if you'd run the build natively. Any `build.py` flags (such as `--customize`) can be appended after the script name.

The first build needs network access because `build.py` downloads the pinned `kobofix.py` helper if it is not already cached in the temporary build directory.

## Native builds

If you do not use the `fntbld` container, install the build dependencies manually for your platform:

- Python 3
- FontForge, available as `fontforge` on `PATH`
- ttfautohint, available as `ttfautohint` on `PATH`
- Python packages: `fonttools`, `brotli`, and `skia-pathops`

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fonttools brotli skia-pathops
python3 build.py
```
