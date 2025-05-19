# Simply Fleet - Diesel Tanker Management

This module extends the Simply Fleet application with diesel tanker management capabilities.

## Features

- Track diesel tankers and their fuel capacity
- Monitor fuel levels with color-coded status indicators:
  - Green: Fuel level ≥ 800 liters
  - Yellow: Fuel level between 400 and 800 liters
  - Red: Fuel level < 400 liters
- Manage fuel refills to tankers
- Track fuel dispensing from tankers to vehicles
- Integration with the existing fuel logs system

## Installation

1. Copy the `simply_fleet_diesel_tanker` folder to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Simply Fleet - Diesel Tanker Management" module

## Usage

### Managing Diesel Tankers

1. Navigate to Simply Fleet > Diesel Tanker
2. Create a new tanker with its capacity
3. Use the "Refill Tanker" button to add fuel to the tanker

### Dispensing Fuel to Vehicles

1. From a diesel tanker's form view, select a vehicle
2. Enter the quantity and odometer information
3. A fuel log will be automatically created

### Accessing from Fuel Logs

1. In the main menu, you'll find a "Diesel Tanker" entry next to "Fuel Logs"
2. When viewing a fuel log with station_type = "diesel_tanker", you'll see a Diesel Tanker button

## Technical Information

The module consists of several models:

- `simply.fleet.diesel.tanker`: Tracks the tankers and their fuel levels
- `simply.fleet.tanker.refill`: Records refilling operations
- `simply.fleet.tanker.dispensing`: Records dispensing operations to vehicles

## Dependencies

- simply_fleet

## Compatibility

This module is compatible with Odoo 17.0 Community Edition.