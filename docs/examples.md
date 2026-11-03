# Dashboards and automations

These examples use Ecobici's *CE-003 Reforma - Insurgentes* and *CE-029 Reforma - Bucareli* stations, on Home Assistant in English. Replace the entity IDs with yours; [Names and entity IDs](entities.md#names-and-entity-ids) shows how to find them.

To use a card, edit your dashboard, add a **Manual** card and paste its YAML. To use an automation, go to **Settings → Automations & scenes**, create an automation and select **⋮ → Edit in YAML**.

## Dashboards

### Stations on a map { #map }

```yaml
type: map
title: Bike stations
entities:
  - entity: sensor.ce_003_reforma_insurgentes_bikes_available
    label_mode: state
  - entity: sensor.ce_029_reforma_bucareli_bikes_available
    label_mode: state
default_zoom: 15
```

`label_mode: state` puts each station's bike count on its marker, instead of the initials of its name. Only the Bikes available sensor has coordinates, so add that one for each station.

### One station at a glance

```yaml
type: entities
title: Reforma - Insurgentes
entities:
  - entity: sensor.ce_003_reforma_insurgentes_bikes_available
    name: Bikes
  - entity: sensor.ce_003_reforma_insurgentes_docks_available
    name: Free docks
  - entity: sensor.ce_003_reforma_insurgentes_occupancy
    name: Occupancy
  - entity: binary_sensor.ce_003_reforma_insurgentes_renting
    name: Renting
  - entity: binary_sensor.ce_003_reforma_insurgentes_returning
    name: Accepting returns
  - entity: sensor.ce_003_reforma_insurgentes_last_reported
    name: Last report
```

If your feed publishes e-bikes, add the station's `_e_bikes_available` sensor too.

### How full it is

A gauge that's red at both ends: an empty station has no bikes to rent, and a full one has no dock for your return.

```yaml
type: gauge
entity: sensor.ce_003_reforma_insurgentes_occupancy
name: Reforma - Insurgentes
min: 0
max: 100
needle: true
segments:
  - from: 0
    color: "#db4437"
  - from: 15
    color: "#ffa600"
  - from: 30
    color: "#43a047"
  - from: 70
    color: "#ffa600"
  - from: 85
    color: "#db4437"
```

### A week of bikes

```yaml
type: statistics-graph
title: Bikes at Reforma - Insurgentes
entities:
  - sensor.ce_003_reforma_insurgentes_bikes_available
days_to_show: 7
period: hour
chart_type: line
stat_types:
  - mean
  - min
  - max
```

The graph uses long-term statistics, so it keeps working after the recorder purges detailed history. Over a week, it shows your station's daily rhythm: when it empties in the morning and when it fills up again.

## Automations

Replace `notify.mobile_app_your_phone` with the notify action of your phone, which the Home Assistant Companion app creates.

### Bike report before work

Every weekday at 7:45, send the number of bikes and free docks at your station.

```yaml
alias: Bike report before work
triggers:
  - trigger: time
    at: "07:45:00"
conditions:
  - condition: time
    weekday: [mon, tue, wed, thu, fri]
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Reforma - Insurgentes
      message: >-
        {{ states('sensor.ce_003_reforma_insurgentes_bikes_available') }} bikes,
        {{ states('sensor.ce_003_reforma_insurgentes_docks_available') }} free docks
```

### Bikes running out

Warn when the station drops below three bikes during the morning commute. The trigger fires when the count crosses below three, not while it stays there.

```yaml
alias: Bikes running out at Reforma - Insurgentes
triggers:
  - trigger: numeric_state
    entity_id: sensor.ce_003_reforma_insurgentes_bikes_available
    below: 3
conditions:
  - condition: time
    after: "07:00:00"
    before: "09:30:00"
    weekday: [mon, tue, wed, thu, fri]
actions:
  - action: notify.mobile_app_your_phone
    data:
      message: >-
        Only {{ states('sensor.ce_003_reforma_insurgentes_bikes_available') }}
        bikes left at Reforma - Insurgentes.
```

### Station stops renting

`from: "on"` ignores the station coming back from unavailable, and `for` ignores short interruptions.

```yaml
alias: Reforma - Insurgentes stopped renting
triggers:
  - trigger: state
    entity_id: binary_sensor.ce_003_reforma_insurgentes_renting
    from: "on"
    to: "off"
    for: "00:10:00"
actions:
  - action: notify.mobile_app_your_phone
    data:
      message: Reforma - Insurgentes isn't renting bikes right now.
```

### Station not reporting { #stale-station }

A station that stops reporting keeps its last counts. To catch that, create a template binary sensor helper: go to **Settings → Devices & services → Helpers**, select **Create helper → Template**, and choose a binary sensor. Use this state template:

```jinja
{% set last = states('sensor.ce_003_reforma_insurgentes_last_reported') | as_datetime %}
{{ last is not none and now() - last > timedelta(minutes=30) }}
```

It turns on when the station hasn't reported for 30 minutes. Use it in automations or show it on a dashboard.

### Total bikes near you

To add up the bikes at several stations, go to **Settings → Devices & services → Helpers** and create a **Combine the state of several sensors** helper. Pick their Bikes available sensors, and choose the **Sum** type.
