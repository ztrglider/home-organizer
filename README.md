# Home Organizer

This repository contains a minimal Home Assistant custom integration called **Room Chore Picker**. It randomly selects a room from your Home Assistant areas each week so chores can be rotated around the house.

## Installation

1. Copy the `custom_components/room_chore_picker` directory into your Home Assistant `config/custom_components` folder or install it via HACS.
2. Restart Home Assistant.
3. After restart a sensor named `sensor.weekly_room_target` will be created.

## Usage

* Call the service `room_chore_picker.shuffle` to manually pick a new room.
* Create an automation that calls this service every weekend to automatically rotate rooms. The integration also schedules a shuffle each Saturday at midnight by default.

The currently recommended room is stored so it persists across restarts.
