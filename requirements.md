# Home Organizer Requirements

## Product vision
Create a lightweight Home Assistant integration that helps households rotate chores fairly by surfacing a single "room of the week" recommendation. Residents should be able to rely on the recommendation persisting across restarts, manually reshuffle when plans change, and tailor the candidate room list to match their actual cleaning rotation.

## Functional requirements
1. Provide a persistent sensor (`sensor.weekly_room_target`) whose state is the recommended room.
2. Automatically pick a new room once per week (Saturday at midnight by default) while also exposing a `room_chore_picker.shuffle` service that can be called on demand.
3. Read the Home Assistant area registry and only recommend valid area names.
4. Allow households to tailor which rooms are eligible by:
   - specifying an explicit allow-list of areas to include in the shuffle; and
   - optionally specifying an exclusion list to remove sensitive rooms from consideration.
5. Persist the recommendation so the sensor survives restarts without losing the previously selected room.
6. Fire an internal event (`room_chore_picker_updated`) whenever a new room is selected so other automations can react.

## Non-functional requirements
- The integration should function without any external dependencies beyond Home Assistant.
- Configuration should be optional; sensible defaults work out-of-the-box.
- Area comparisons should be case-insensitive to make configuration forgiving.
- Documentation must cover configuration options and describe expected behavior.

## Phase 1 priorities
- Deliver configuration-driven inclusion/exclusion controls for areas.
- Update documentation to reflect the new controls.
- Prepare the codebase for upcoming test coverage and diagnostics improvements.
