# Computer Vision — Sprint 11.4

**Module:** `applications/drone_platform/vision/`  
**Version:** Drone Platform `1.3.0-alpha`

## Overview

Engineering computer-vision facade for multi-camera UAV perception: capture, stream, frame processing, image pipelines, and object detection/tracking.

## Components

- Vision Manager · Camera Manager · Video Stream Manager · Frame Processor · Image Pipeline
- Multi / Stereo / Thermal / Night Vision / Depth camera support
- Object Detector + class-specific detectors (vehicle, person, aircraft, ship, building, road, tree, power line, landing zone, obstacle)
- Target tracking · Multi-object tracking · Classification

## API

`/api/drone/v1/vision`, `/vision/cameras`, `/streams`, `/frames`, `/detect`, `/track`

## Related

[NAVIGATION_AI.md](NAVIGATION_AI.md) · [AUTONOMOUS_FLIGHT.md](AUTONOMOUS_FLIGHT.md) · [SLAM_MAPPING.md](SLAM_MAPPING.md)
