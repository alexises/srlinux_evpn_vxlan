"""Main package."""

from argparse import ArgumentParser, Namespace

from rich.console import Console

from .compute.compute import YangController
from .compute.template_scanner import scan
from .idempotency import IdempotencyManager
from .metamodel import get_model
from .yang_model.templates import scan_yang


def parse_args() -> Namespace:
    """Parse configuration.

    Returns:
        Namespace: parsed config.
    """
    args = ArgumentParser("srlab YANG config management")
    args.add_argument("configfile", help="Configuration file")
    args.add_argument("--host", "-H", action="append", default=[])
    args.add_argument("--no-dryrun", "-D", action="store_true", default=False)
    args.add_argument("--show-config", "-C", action="store_true", default=False)

    return args.parse_args()


def main() -> None:
    """Main entrypoint."""
    console = Console()
    args = parse_args()
    scan("yang_srlab.templates")
    scan_yang("yang_srlab.yang_templates")

    model = get_model(args.configfile)

    console.log("read metamodel", style="bold yellow")
    controller = YangController(model)
    console.log("transform meta model into configuration", style="bold yellow")
    computed_elements = controller.compute_all(args.host)
    manager = IdempotencyManager(
        computed_elements,
        console,
        with_config_print=args.show_config,
        with_commit=args.no_dryrun,
    )
    manager.run()


if __name__ == "__main__":
    main()
