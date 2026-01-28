"""HomeKit pairing utility for initial device setup using aiohomekit."""

import argparse
import asyncio
import json
import sys

from aiohomekit import Controller
from aiohomekit.model.status_flags import StatusFlags
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
from zeroconf import ServiceListener

def add_to_shepherd(pairing_data: dict, name: str) -> bool:
    """Add HomeKit pairing to Shepherd using shepherd CLI.

    Args:
        pairing_data: The pairing data dict
        name: Name for this server in Shepherd

    Returns:
        True if successful, False otherwise
    """
    import subprocess
    import shutil

    if not shutil.which("shepherd"):
        print("Shepherd CLI not found in PATH")
        return False

    try:
        cmd = [
            "shepherd", "smcp", "add",
            name,
            "homekit-smcp-server",
            "--cred", f"HOMEKIT_PAIRING_DATA={json.dumps(pairing_data)}",
            "--cred", "READ_ONLY_MODE=false"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Added '{name}' to Shepherd")
            return True
        else:
            print(f"Error adding to Shepherd: {result.stderr or result.stdout}")
            return False

    except Exception as e:
        print(f"Error running shepherd: {e}")
        return False

HAP_TYPE_TCP = "_hap._tcp.local."
HAP_TYPE_UDP = "_hap._udp.local."


class _HapListener(ServiceListener):
    """Empty listener required by zeroconf browser."""
    def add_service(self, zc, type_, name):
        pass
    def remove_service(self, zc, type_, name):
        pass
    def update_service(self, zc, type_, name):
        pass


async def discover_devices(timeout: int = 10) -> list:
    """Discover HomeKit devices on the network."""
    print(f"Discovering HomeKit devices (timeout: {timeout}s)...")

    # Set up zeroconf with browsers for both HAP protocols
    azc = AsyncZeroconf()
    listener = _HapListener()
    browser_tcp = AsyncServiceBrowser(azc.zeroconf, HAP_TYPE_TCP, listener)
    browser_udp = AsyncServiceBrowser(azc.zeroconf, HAP_TYPE_UDP, listener)

    controller = Controller(async_zeroconf_instance=azc)
    await controller.async_start()

    devices = []
    try:
        # Wait for discovery to populate - aiohomekit's async_discover
        # only yields what's already cached, doesn't wait for new devices
        await asyncio.sleep(timeout)

        # Now collect discovered devices
        async for device in controller.async_discover():
            devices.append(device)
    finally:
        await controller.async_stop()
        await browser_tcp.async_cancel()
        await browser_udp.async_cancel()
        await azc.async_close()

    return devices


async def list_devices_async(timeout: int = 10):
    """List discovered HomeKit devices."""
    devices = await discover_devices(timeout)

    if not devices:
        print("No HomeKit devices found on the network.")
        print("Make sure your HomeKit devices are powered on and on the same network.")
        return

    print(f"\nFound {len(devices)} HomeKit device(s):\n")
    print("-" * 80)

    for i, device in enumerate(devices, 1):
        desc = device.description
        paired = not (desc.status_flags & StatusFlags.UNPAIRED)
        print(f"Device {i}:")
        print(f"  Name:        {desc.name}")
        print(f"  ID:          {desc.id}")
        print(f"  Model:       {desc.model}")
        print(f"  Category:    {desc.category}")
        print(f"  Config Num:  {desc.config_num}")
        print(f"  State Num:   {desc.state_num}")
        print(f"  Status:      {'Paired' if paired else 'Unpaired'}")
        print(f"  Address:     {desc.address}:{desc.port}")
        print("-" * 80)


async def pair_device_async(device_id: str, pin: str, alias: str = None, timeout: int = 10) -> dict:
    """Pair with a HomeKit device.

    Args:
        device_id: The device's pairing ID (from discovery)
        pin: The 8-digit setup code (XXX-XX-XXX format or without dashes)
        alias: Optional alias for the pairing (defaults to device_id)
        timeout: Discovery timeout in seconds

    Returns:
        Pairing data as a dictionary
    """
    # Normalize PIN format
    pin = pin.replace("-", "")
    if len(pin) != 8:
        raise ValueError("PIN must be 8 digits")

    # Format as XXX-XX-XXX for aiohomekit
    formatted_pin = f"{pin[:3]}-{pin[3:5]}-{pin[5:]}"

    alias = alias or device_id

    print(f"Searching for device: {device_id}")

    # Set up zeroconf with browsers for both HAP protocols
    azc = AsyncZeroconf()
    listener = _HapListener()
    browser_tcp = AsyncServiceBrowser(azc.zeroconf, HAP_TYPE_TCP, listener)
    browser_udp = AsyncServiceBrowser(azc.zeroconf, HAP_TYPE_UDP, listener)

    controller = Controller(async_zeroconf_instance=azc)
    await controller.async_start()

    try:
        # Wait for discovery to populate
        await asyncio.sleep(timeout)

        # Find the device
        target_device = None
        async for device in controller.async_discover():
            if device.description.id.lower() == device_id.lower():
                target_device = device
                break

        if not target_device:
            raise ValueError(f"Device {device_id} not found on network")

        desc = target_device.description
        paired = not (desc.status_flags & StatusFlags.UNPAIRED)

        if paired:
            raise ValueError(f"Device {device_id} is already paired")

        print(f"Found device: {desc.name}")
        print(f"Using PIN: {formatted_pin}")
        print(f"Alias: {alias}")

        # Start pairing - returns a finish_pairing coroutine function
        print("Starting pairing process...")
        finish_pairing = await target_device.async_start_pairing(alias)

        # Finish pairing with PIN
        print("Completing pairing with PIN...")
        pairing = await finish_pairing(formatted_pin)

        # Export pairing data
        pairing_data = {
            "alias": alias,
            "AccessoryPairingID": pairing.pairing_data.get("AccessoryPairingID"),
            "AccessoryLTPK": pairing.pairing_data.get("AccessoryLTPK"),
            "iOSPairingId": pairing.pairing_data.get("iOSPairingId"),
            "iOSDeviceLTSK": pairing.pairing_data.get("iOSDeviceLTSK"),
            "iOSDeviceLTPK": pairing.pairing_data.get("iOSDeviceLTPK"),
            "AccessoryIP": pairing.pairing_data.get("AccessoryIP"),
            "AccessoryPort": pairing.pairing_data.get("AccessoryPort"),
            "Connection": "IP",
        }

        return pairing_data
    finally:
        await controller.async_stop()
        await browser_tcp.async_cancel()
        await browser_udp.async_cancel()
        await azc.async_close()


def main():
    """Main entry point for the pairing utility."""
    parser = argparse.ArgumentParser(
        description="HomeKit device pairing utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover devices on the network
  homekit-smcp-pair --discover

  # Pair with a device
  homekit-smcp-pair --pair --device-id AA:BB:CC:DD:EE:FF --pin 123-45-678

  # Pair and save to file
  homekit-smcp-pair --pair --device-id AA:BB:CC:DD:EE:FF --pin 12345678 --output pairing.json

  # Pair with custom alias
  homekit-smcp-pair --pair --device-id AA:BB:CC:DD:EE:FF --pin 123-45-678 --alias "living-room-light"
"""
    )

    parser.add_argument(
        "--discover", "-d",
        action="store_true",
        help="Discover HomeKit devices on the network"
    )
    parser.add_argument(
        "--pair", "-p",
        action="store_true",
        help="Pair with a HomeKit device"
    )
    parser.add_argument(
        "--device-id",
        help="Device pairing ID (from discovery)"
    )
    parser.add_argument(
        "--pin",
        help="8-digit setup code (XXX-XX-XXX or XXXXXXXX)"
    )
    parser.add_argument(
        "--alias",
        help="Alias for the pairing (defaults to device ID)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for pairing data (defaults to stdout)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=10,
        help="Discovery timeout in seconds (default: 10)"
    )

    args = parser.parse_args()

    if args.discover:
        asyncio.run(list_devices_async(args.timeout))
        return

    if args.pair:
        if not args.device_id:
            print("Error: --device-id is required for pairing", file=sys.stderr)
            sys.exit(1)
        if not args.pin:
            print("Error: --pin is required for pairing", file=sys.stderr)
            sys.exit(1)

        try:
            pairing_data = asyncio.run(
                pair_device_async(args.device_id, args.pin, args.alias, args.timeout)
            )

            # Output pairing data
            json_output = json.dumps(pairing_data, indent=2)

            if args.output:
                with open(args.output, "w") as f:
                    f.write(json_output)
                print(f"\nPairing successful! Data saved to: {args.output}")
            else:
                print("\nPairing successful! Pairing data:\n")
                print(json_output)

            # Ask if user wants to add to Shepherd
            print()
            response = input("Add to Shepherd? [Y/n]: ").strip().lower()
            if response != 'n':
                name = input("Server name for Shepherd [homekit]: ").strip() or "homekit"
                add_to_shepherd(pairing_data, name)

        except Exception as e:
            print(f"Error: Pairing failed: {e}", file=sys.stderr)
            sys.exit(1)

        return

    # If no action specified, show help
    parser.print_help()


if __name__ == "__main__":
    main()
