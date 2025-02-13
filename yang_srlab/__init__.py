"""Main package."""

from argparse import ArgumentParser, Namespace

from .dataclass.interface import InterfaceContainer
from .metamodel import get_model
from .yang import Action, SRLClient


def parse_args() -> Namespace:
    """Parse configuration.

    Returns:
        Namespace: parsed config.
    """
    args = ArgumentParser("srlab YANG config management")
    args.add_argument("configfile", help="Configuration file")

    return args.parse_args()


def main() -> None:
    """Main entrypoint."""
    args = parse_args()
    model = get_model(args.configfile)

    switch = model.fabrics[0].lifs[0]
    ifaces = InterfaceContainer(20)
    yang_data = ifaces.to_yang()

    print(
        yang_data.model_dump_json(
            indent=2,
            exclude_none=True,
            exclude_unset=True,
        ),
    )
    print(f"connect to : {switch.address}")
    with SRLClient(host=str(switch.address)) as client:
        client.add_set_command(action=Action.REPLACE, path="/interface", value=yang_data)
        diff_data = client.send_diff_request()
    print(diff_data.json()["result"][0])
    # print(diff_data.json()["result"][0])


if __name__ == "__main__":
    main()
