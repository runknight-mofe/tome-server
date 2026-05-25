-- ============================================================================
-- Aether / Tome Server — device_types seed data
-- ============================================================================
-- Populates the device_types table with known UWB hardware platforms.
--
-- ranging_method column stores the RangingMethod enum ordinal:
--   0  TWR       Two-Way Ranging
--   1  TDOA      Time Difference of Arrival
--   2  TWR_TDOA  Hardware supports both; mode selected at runtime
--
-- supports_aoa: TRUE when the chipset can report Angle of Arrival in addition
--               to distance.  Drives whether the fusion engine uses angle
--               observations in the position estimate.
--
-- max_update_rate_hz: the hardware datasheet ceiling for ranging cycles per
--                     second.  The MOFE scheduler will not exceed this value
--                     when configuring the ranging cycle for a device.
--
-- typical_accuracy_m: published or measured 1-sigma ranging accuracy under
--                     normal LOS conditions.  Seeds the process noise
--                     covariance in the Kalman filter; per-device calibration
--                     will override this at deployment time.
--
-- ordinal assignment strategy:
--   0–9    Reserved / generic / emulated device classes
--   10–99  Qorvo / DecaWave chipset family (DW1000, DW3000 series)
--   100–199 Sewio RTLS family
--   200–299 Pozyx family
--   300–399 Ubisense family
--   400–499 BeSpoon / STM family
--   500–599 Apple / Nearby Interaction chipsets
--   600–699 NXP Trimension family
--   900–999 Custom / in-house hardware
-- ============================================================================

INSERT INTO device_types (
    ordinal, name, description,
    manufacturer, ranging_method,
    supports_aoa, max_update_rate_hz, typical_accuracy_m
)
VALUES

-- --------------------------------------------------------------------------
-- 0–9  Generic / emulated
-- --------------------------------------------------------------------------

(0,
 'EMULATED_GENERIC',
 'Software-emulated device with no physical hardware. Used for simulation, '
 'testing, and development environments where real UWB hardware is unavailable.',
 'Aether Software', 0,   -- TWR
 FALSE, 100.0, 0.01),    -- negligible error by design

(1,
 'EMULATED_AoA',
 'Software-emulated device with simulated Angle of Arrival output. '
 'Used for validating AoA-aware fusion pipelines without physical hardware.',
 'Aether Software', 0,   -- TWR
 TRUE, 100.0, 0.01),

-- --------------------------------------------------------------------------
-- 10–99  Qorvo / DecaWave
-- --------------------------------------------------------------------------

(10,
 'DW1000',
 'DecaWave DW1000 IEEE 802.15.4-2011 UWB transceiver. First-generation '
 'single-chip UWB solution; widely deployed in RTLS infrastructure. '
 'Does not support native AoA; angle estimation requires multi-antenna arrays.',
 'Qorvo (DecaWave)', 0,  -- TWR
 FALSE, 100.0, 0.10),

(11,
 'DWM1000',
 'DecaWave DWM1000 module — DW1000 chip with integrated antenna, crystal, '
 'and RF circuitry. Drop-in module for rapid prototyping and production. '
 'Identical UWB performance to the bare DW1000 IC.',
 'Qorvo (DecaWave)', 0,  -- TWR
 FALSE, 100.0, 0.10),

(12,
 'DWM1001',
 'DecaWave DWM1001 module — DW1000 with integrated Nordic nRF52832 MCU and '
 'BLE. Runs the DecaWave PANS firmware stack out of the box; supports '
 'two-way ranging and TDOA via dedicated anchor listener mode.',
 'Qorvo (DecaWave)', 2,  -- TWR_TDOA
 FALSE, 100.0, 0.10),

(13,
 'DWM1001-DEV',
 'DWM1001 mounted on a development board with USB, LEDs, and expansion '
 'headers. Functionally identical to DWM1001; intended for bench evaluation '
 'and mesh bring-up.',
 'Qorvo (DecaWave)', 2,  -- TWR_TDOA
 FALSE, 100.0, 0.10),

(14,
 'DW3000',
 'Qorvo DW3000 IEEE 802.15.4z UWB transceiver. Second-generation chip with '
 'enhanced accuracy, lower power, and native support for IEEE 802.15.4z '
 'HRP UWB PHY. Supports AoA via Phase Difference of Arrival on dual-antenna '
 'configurations.',
 'Qorvo', 0,             -- TWR (802.15.4z STS-enabled TWR)
 TRUE, 200.0, 0.05),

(15,
 'DWM3000',
 'Qorvo DWM3000 module — DW3000 chip with integrated antenna and RF frontend. '
 'Compact form factor for tag and anchor designs requiring improved accuracy '
 'over DW1000-based modules.',
 'Qorvo', 0,             -- TWR
 TRUE, 200.0, 0.05),

(16,
 'DWM3001C',
 'Qorvo DWM3001C — DW3000 with integrated nRF52833 MCU, BLE 5.3, and '
 'accelerometer. Targets IEEE 802.15.4z FiRa-compliant ranging with '
 'concurrent BLE for configuration and telemetry.',
 'Qorvo', 0,             -- TWR
 TRUE, 200.0, 0.05),

(17,
 'QM33120WDK1',
 'Qorvo QM33120 development kit — next-generation UWB transceiver evaluation '
 'platform. Supports STS-based secure ranging per IEEE 802.15.4z and '
 'two-antenna AoA measurement.',
 'Qorvo', 0,             -- TWR
 TRUE, 250.0, 0.04),

-- --------------------------------------------------------------------------
-- 100–199  Sewio RTLS
-- --------------------------------------------------------------------------

(100,
 'SEWIO_ANCHOR_UNI',
 'Sewio Universal Anchor — infrastructure node for Sewio RTLS. Operates in '
 'TDOA listener mode; timestamps tag transmissions using a hardware clock '
 'synchronised across the anchor network.',
 'Sewio Networks', 1,    -- TDOA
 FALSE, 166.0, 0.30),

(101,
 'SEWIO_TAG_SPORT',
 'Sewio Sport Tag — wearable UWB tag optimised for high-density personnel '
 'tracking in sports analytics environments. Transmits UWB blink frames '
 'received by Sewio anchors for TDOA location calculation.',
 'Sewio Networks', 1,    -- TDOA
 FALSE, 166.0, 0.30),

(102,
 'SEWIO_TAG_INDUSTRY',
 'Sewio Industry Tag — ruggedised wearable / asset tag with IP67 rating '
 'and extended battery life. Same TDOA blink architecture as Sport Tag; '
 'intended for manufacturing and logistics deployments.',
 'Sewio Networks', 1,    -- TDOA
 FALSE, 100.0, 0.30),

-- --------------------------------------------------------------------------
-- 200–299  Pozyx
-- --------------------------------------------------------------------------

(200,
 'POZYX_CREATOR',
 'Pozyx Creator tag and anchor — DW1000-based Arduino-compatible module. '
 'Designed for rapid UWB prototyping; ships with open-source firmware and '
 'TWR-based ranging library.',
 'Pozyx Labs', 0,        -- TWR
 FALSE, 100.0, 0.10),

(201,
 'POZYX_ENTERPRISE_ANCHOR',
 'Pozyx Enterprise Anchor — infrastructure-grade UWB anchor with PoE, '
 'Ethernet backhaul, and hardware timestamping. Supports both TWR and TDOA '
 'operating modes selectable per deployment.',
 'Pozyx Labs', 2,        -- TWR_TDOA
 FALSE, 100.0, 0.15),

(202,
 'POZYX_ENTERPRISE_TAG',
 'Pozyx Enterprise Tag — battery-powered UWB tag with integrated IMU '
 'and BLE. Supports both TWR (direct ranging) and TDOA (blink) modes '
 'depending on anchor network configuration.',
 'Pozyx Labs', 2,        -- TWR_TDOA
 FALSE, 100.0, 0.15),

-- --------------------------------------------------------------------------
-- 300–399  Ubisense
-- --------------------------------------------------------------------------

(300,
 'UBISENSE_SERIES_7000',
 'Ubisense Series 7000 RTLS sensor — infrastructure unit supporting '
 'TDOA-based location with proprietary ultra-wideband signalling. '
 'Includes integrated AoA measurement via multi-element antenna array; '
 'provides 2D and 3D position with sub-30 cm accuracy.',
 'Ubisense', 1,          -- TDOA
 TRUE, 50.0, 0.15),

(301,
 'UBISENSE_DIMENSION4_TAG',
 'Ubisense Dimension4 UWB tag — active transponder worn or mounted on '
 'assets tracked by Series 7000 or Dimension4 sensors. Transmits UWB '
 'blink frames at configurable intervals; sensors compute position via TDOA.',
 'Ubisense', 1,          -- TDOA
 FALSE, 50.0, 0.15),

-- --------------------------------------------------------------------------
-- 400–499  BeSpoon / STMicroelectronics
-- --------------------------------------------------------------------------

(400,
 'BESPOON_SP1ML',
 'BeSpoon SP1ML (now ST) UWB module — sub-GHz and UWB dual-radio module '
 'for industrial asset tracking. Two-way ranging with ranging rate up to '
 '100 Hz. Compact SMD form factor for OEM integration.',
 'STMicroelectronics (BeSpoon)', 0,  -- TWR
 FALSE, 100.0, 0.10),

(401,
 'ST_X-NUCLEO-NFC06A1',
 'STMicroelectronics X-NUCLEO-NFC06A1 UWB expansion board with ST33G1M2 '
 'secure element. Intended for evaluation of UWB secure ranging in '
 'access control and payment proximity applications.',
 'STMicroelectronics', 0,   -- TWR
 FALSE, 50.0, 0.20),

-- --------------------------------------------------------------------------
-- 500–599  Apple / Nearby Interaction
-- --------------------------------------------------------------------------

(500,
 'APPLE_U1',
 'Apple U1 chip — UWB transceiver integrated into iPhone 11 and later, '
 'AirTag, HomePod mini, and Apple Watch Ultra. Implements IEEE 802.15.4z '
 'TWR via the Nearby Interaction framework. AoA supported on hardware with '
 'dual-antenna arrays (iPhone 11 and later). Not directly programmable; '
 'accessed via CoreNearbyInteraction API only.',
 'Apple', 0,             -- TWR
 TRUE, 60.0, 0.05),

(501,
 'APPLE_AIRTAG',
 'Apple AirTag — consumer UWB asset tracker using the U1 chip in passive '
 'beacon mode. Responds to TWR ranging requests initiated by iPhone. '
 'No programmable interface; included for completeness when an iOS device '
 'participates in a mesh as the ranging initiator.',
 'Apple', 0,             -- TWR
 FALSE, 60.0, 0.05),

-- --------------------------------------------------------------------------
-- 600–699  NXP Trimension
-- --------------------------------------------------------------------------

(600,
 'NXP_SR040',
 'NXP SR040 UWB transceiver — IEEE 802.15.4z HRP UWB PHY supporting '
 'FiRa consortium ranging profiles. Includes integrated secure element '
 'for cryptographic ranging session management. Supports AoA via phase '
 'difference measurement on dual antennas.',
 'NXP Semiconductors', 0,   -- TWR
 TRUE, 200.0, 0.05),

(601,
 'NXP_SR150',
 'NXP SR150 — NXP Trimension UWB transceiver with enhanced AoA and '
 'multi-device ranging. Supports FiRa, CCC (Car Connectivity Consortium), '
 'and IEEE 802.15.4z. Target applications: automotive keyless entry, '
 'smart home, and RTLS.',
 'NXP Semiconductors', 0,   -- TWR
 TRUE, 200.0, 0.04),

(602,
 'NXP_UM11225_ANCHOR',
 'NXP UWB anchor reference design based on SR150 — four-antenna AoA '
 'array providing azimuth and elevation angle measurement in addition to '
 'two-way range. Intended as infrastructure node in FiRa-compliant systems.',
 'NXP Semiconductors', 0,   -- TWR
 TRUE, 200.0, 0.04),

-- --------------------------------------------------------------------------
-- 900–999  Custom / in-house
-- --------------------------------------------------------------------------

(900,
 'CUSTOM_TWR_NODE',
 'Placeholder for a custom in-house TWR node not otherwise catalogued. '
 'Update name, description, manufacturer, and capability fields to match '
 'the actual hardware before deployment.',
 'Custom', 0,            -- TWR
 FALSE, NULL, NULL),

(901,
 'CUSTOM_TDOA_NODE',
 'Placeholder for a custom in-house TDOA node not otherwise catalogued. '
 'Update name, description, manufacturer, and capability fields to match '
 'the actual hardware before deployment.',
 'Custom', 1,            -- TDOA
 FALSE, NULL, NULL)

ON CONFLICT (ordinal) DO NOTHING;