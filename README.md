# unifi-mqtt

Translate events from Unifi equipment into an MQTT stream.

```shell
unifi-mqtt --help
```

## General Thinking

Take a set of events, from any available Unifi service, and turn them into a reasonable representation within MQTT.

Some of this will be doing via Unifi event streams, some of it may require polling information. Because it's not uniform that means this project will need to determine some payloads itself. An open question remains on whether the project should determine _all_ payloads, but for API compatibility that would certainly be valuable.

Right now the approach is to take an event (`EVT_WU_Disconnected`) and translate it into an mqtt topic (`{prefix}/unifi/network/client/connected`). The payload would have to include a number of details in the upstream event, augment them with additional meta information (e.g. `WU` vs `LU` in the connected event), and coerce them into a predictable format.

Note: The above assumes limited knowledge of MQTT principals, and its possible we may want to tweak topics.
