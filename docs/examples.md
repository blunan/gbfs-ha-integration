# Dashboards and Automations

Practical dashboard cards and automations using the integration's sensors.

Replace the example entity IDs (`sensor.ce_003_reforma_insurgentes_...`) with your station's actual entities, which can be found on each station's device page.

## Dashboard Cards

### Stations on a Map { #map }

Plot stations on a Home Assistant Map card. Setting `label_mode: state` displays each station's live bike count directly on its marker:

```yaml
type: map
title: Bike Stations
entities:
  - entity: sensor.ce_003_reforma_insurgentes_bikes_available
    label_mode: state
  - entity: sensor.ce_029_reforma_bucareli_bikes_available
    label_mode: state
default_zoom: 15
```

!!! note "Coordinates"
    Only the **Bikes available** sensor carries coordinates, ensuring exactly one pin per station on the map.

### Station Overview (Entities Card)

Display all key metrics for a station in a single card:

```yaml
type: entities
title: Reforma - Insurgentes
entities:
  - entity: sensor.ce_003_reforma_insurgentes_bikes_available
    name: Bikes
  - entity: sensor.ce_003_reforma_insurgentes_e_bikes_available
    name: E-bikes
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

### Station Occupancy Gauge

A gauge highlighting extreme conditions — empty stations (no bikes to rent) or full stations (no docks to return):

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

### Weekly Usage Statistics Graph

Track historical station availability using Home Assistant long-term statistics:

```yaml
type: statistics-graph
title: Bike Availability Trend
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

## Automations

Replace `notify.mobile_app_your_phone` with your mobile device's notify service or action.

### Morning Commute Briefing

Send a notification every weekday morning with bike and dock counts:

```yaml
alias: Morning Bike Briefing
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
        {{ states('sensor.ce_003_reforma_insurgentes_docks_available') }} free docks available.
```

### Low Bike Availability Warning

Alert when station bike count drops below 3 during the morning rush:

```yaml
alias: Low Bike Alert
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
      title: Bike Shortage Warning
      message: >-
        Only {{ states('sensor.ce_003_reforma_insurgentes_bikes_available') }}
        bikes left at Reforma - Insurgentes.
```

### Rental Interruption Alert

Alert when a station goes out of service or halts rentals for more than 10 minutes:

```yaml
alias: Station Stopped Renting
triggers:
  - trigger: state
    entity_id: binary_sensor.ce_003_reforma_insurgentes_renting
    from: "on"
    to: "off"
    for: "00:10:00"
actions:
  - action: notify.mobile_app_your_phone
    data:
      message: Reforma - Insurgentes is temporarily not renting bikes.
```

### Stale Station Detection Helper { #stale-station }

If a station stops reporting, its counts remain static at the last known values. To flag stale data, create a Template Binary Sensor helper in **Settings → Devices & services → Helpers → Create helper → Template → Template a binary sensor**:

```jinja
{% set last = states('sensor.ce_003_reforma_insurgentes_last_reported') | as_datetime %}
{{ last is not none and now() - last > timedelta(minutes=30) }}
```

This sensor turns `on` if the station has not reported updates for over 30 minutes.

### Neighborhood Bike Aggregation

To calculate the total number of bikes across nearby stations:

1. Go to **Settings → Devices & services → Helpers**.
2. Select **Create helper → Combine the state of several sensors**.
3. Add the `bikes_available` entities of your nearby stations and set the statistic type to **Sum**.
