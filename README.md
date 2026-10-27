# city-timelapse

Render engine for an illustrated city-timelapse series: a three.js scene of a city through time, rendered headless in parallel on GitHub Actions.

- `engine/city.html`: the engine. `engine/render.mjs`: headless renderer.
- `chicago/`: scene builder (City of Chicago and OpenStreetMap open data) and the episode timeline.
- `jobs/render.json`: pushing a change renders the timeline in parallel slices and publishes them to the `slices` branch.

Data: City of Chicago building footprints (open data), © OpenStreetMap contributors (ODbL). Earlier eras are illustrative reconstructions.
