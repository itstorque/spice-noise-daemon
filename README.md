# spice-noise-daemon
Noise Component Generator and Entropy Daemon for LTSpice

Daemon creates .asy and .lib files. Run in directory of a project and use components as a voltage/current source.
Change what noise sources are in the `noise/noise_sources.yaml` file.
Running the daemon in live mode adds entropy between runs to rewrite csv based on noise
distribution defined in the yaml file.
