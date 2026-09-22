SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory authoring guidance

All content in this document is non-normative authoring guidance. The canonical wire format remains the [binary TLV manifest envelope](envelope.md); authoring names and example IDs do not assign wire values.

## YAML source description

For each concrete node inventory, provide a YAML source description for review
alongside the normative tables. YAML is authoring input only; the wire format
remains canonical binary TLV. The minimum shape is:

```yaml
format: 1
revision: 1
resources:
  - id: 1
    kind: gas_cell
    properties:
      measured_gas: oxygen
      technology: galvanic
      interface: analog_voltage
    outputs:
      - publisher_id: 1
        semantic: cell_voltage
        origin: raw_interface
        unit: millivolts
        value_type: f32
      - publisher_id: 2
        semantic: gas_partial_pressure
        gas: oxygen
        origin: derived_local
        transform: oxygen_cell_calibration
        unit: millibars
        value_type: f32
    relations:
      - kind: derived_from
        subject: { resource: 1, publisher: 2 }
        target: { resource: 1, publisher: 1 }

  - id: 2
    kind: gas_cell
    properties:
      measured_gas: carbon_dioxide
      technology: electrochemical
      interface: ppm_output
    outputs:
      - publisher_id: 3
        semantic: gas_concentration
        gas: carbon_dioxide
        origin: direct_sensor
        unit: ppm
        value_type: f32
      - publisher_id: 4
        semantic: gas_partial_pressure
        gas: carbon_dioxide
        origin: derived_local
        transform: ppm_to_partial_pressure
        unit: millibars
        value_type: f32
    relations:
      - kind: derived_from
        subject: { resource: 2, publisher: 4 }
        target: { resource: 2, publisher: 3 }
      - kind: requires_input
        subject: { resource: 2, publisher: 4 }
        target: { resource: 6, publisher: 60 }

  - id: 3
    kind: gas_cell
    properties:
      measured_gas: oxygen
      technology: digital
      interface: digital_partial_pressure
    outputs:
      - publisher_id: 5
        semantic: gas_partial_pressure
        gas: oxygen
        origin: direct_sensor
        unit: millibars
        value_type: f32

  - id: 20
    kind: decompression_engine
    outputs:
      - publisher_id: 40
        semantic: gas_tissue_saturation
        origin: derived_local
        value_type: structured_snapshot
        shape: [4, 32]
        dimensions:
          - name: gas
            values: [oxygen, nitrogen, helium, carbon_dioxide]
          - name: tissue
            count: 32
        element:
          value_type: u8
          unit: percent
        encoded_length: 132
        delivery_class: advisory
        minimum_request_interval_ms: 5000
```

The example names are illustrative until their registry IDs and exact wire
constraints are assigned. Future content contributions should provide the
following registries first:

1. `resource_kind`: physical sensors, actuators, derived values, software
   modules, and interface/controller resources.
2. `semantic_id`: measurements, states, commands, and derived quantities.
3. `unit_id`: canonical units and conversion policy, reusing telemetry units
   where they have the exact same meaning.
4. `value_type`: scalar and structured wire representations, including size
   and encoding rules.
5. `output_origin`: direct sensor, raw interface, local derivation, or
   external derivation.
6. `transform_id`: calibration and conversion functions such as cell
   calibration and ppm-to-partial-pressure.
7. `gas_species`: gases measured or represented by an output.
8. `output_shape`: scalar, fixed array, matrix, packed tissue vector, or
   structured snapshot dimensions.
9. `relation_kind`: resource-to-resource and output-to-output relationships.
10. `parameter_id`: configuration properties and their ownership.
11. Constraint kinds: numeric bounds, enumerations, cardinality, table shapes,
   and update requirements.

A registry entry is not complete until its stable ID, wire representation,
validation rules, and semantic meaning are specified.
