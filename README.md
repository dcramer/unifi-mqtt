# unifi-mqtt

Translate events from Unifi applications into an MQTT stream.

```shell
unifi-mqtt --help
```

## Goals

MQTT is a standard format for IoT, but not every hardware provider has baked in support. This project aims to add MQTT support to Unifi by creating a broker between the protocols.

This allows us to more easily introspect whats going on with our Unifi devices, and decouples integrations from requiring something like Home Assistant to perform basic actions.

The intent is to be able to support all services ('applications') which are available within the Unifi controller. As of right now this includes:

- Network
- Protect
- Access
- Talk

## General Thinking

Take a set of events, from any available Unifi service, and turn them into a reasonable representation within MQTT.

Some of this will be doing via Unifi event streams, some of it may require polling information. Because it's not uniform that means this project will need to determine some payloads itself. An open question remains on whether the project should determine _all_ payloads, but for API compatibility that would certainly be valuable.

Right now the approach is to take an event (`EVT_WU_Disconnected`) and translate it into an mqtt topic (`{prefix}/network/client/connected`). The payload would have to include a number of details in the upstream event, augment them with additional meta information (e.g. `WU` vs `LU` in the connected event), and coerce them into a predictable format.

Note: The above assumes limited knowledge of MQTT principles, and its possible we may want to tweak topics.

Additionally we'd like to provide some form of service actions by publishing to certain streams. This still needs more thought on what kind of actions make sense, and what format is applicable.

## Topics

All payloads will include the following fields:

- `service` - the service name (e.g. `network` or `protect`)
- `event` - the internal event name (e.g. `EVT_WU_Disconnected`)
- `ts` - the timestamp of the event in milliseconds
- `raw` - the original event payload

The following payloads are currently published:

- `<service>/connected` - on connection established
- `<service>/disconnected` - on connection broken
- `network/wifi/<network>/client/<hostname>` - on connect/disconnect
- `network/lan/<network>/client/<hostname>` - on connect/disconnect
- `access/device/<device>/unlock` - on successful/unsuccessful unlock
- `access/target/<target>/unlock` - on successful/unsuccessful unlock
