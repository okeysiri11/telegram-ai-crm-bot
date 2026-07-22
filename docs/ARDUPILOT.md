# ArduPilot Integration (Sprint 11.2)

**Engine:** `applications/drone_platform/firmware/ardupilot/`  
**API prefix:** `/api/drone/v1/ardupilot/`

## Overview

ArduPilot engineering workspace inside Drone Platform: projects, parameter database, mode library, vehicle profiles, mission library, and branch manager.

## Vehicle support

Plane · Copter · Rover · Boat · Sub · Custom

## Features

- ArduPilot Project Manager
- Parameter Database (seeded core params per vehicle)
- Mode Library
- Vehicle Profiles
- Mission Library templates
- Firmware Branch Manager

## REST

- `GET|POST /ardupilot/projects`
- `GET /ardupilot/parameters?vehicle=copter`
- `GET /ardupilot/modes?vehicle=plane`
- `GET|POST /ardupilot/vehicles`
- `GET|POST /ardupilot/branches`

## Policy

Engineering assistance only — configuration and analysis for legitimate UAV development, testing, and maintenance.
