import irsdk
import numpy as np


class ReferenceLap:
    """Loads a .ibt file and exposes brake/throttle indexed by LapDistPct."""

    def __init__(self, path: str):
        self.path = path
        self.dist = None    # np.array of LapDistPct values
        self.throttle = None
        self.brake = None
        self._load(path)

    def _load(self, path: str):
        ir = irsdk.IBT()
        ir.open(path)

        dist     = ir.get('LapDistPct')
        throttle = ir.get('Throttle')
        brake    = ir.get('Brake')

        ir.close()

        if dist is None or throttle is None or brake is None:
            raise ValueError(f"Could not read telemetry channels from {path}")

        dist     = np.array(dist,     dtype=np.float32)
        throttle = np.array(throttle, dtype=np.float32)
        brake    = np.array(brake,    dtype=np.float32)

        # Keep only the fastest (lowest lap time) complete lap
        self.dist     = dist
        self.throttle = throttle
        self.brake    = brake

    def sample_at(self, lap_dist_pct: float) -> tuple[float, float]:
        """Return (throttle, brake) at the given track position via nearest-sample lookup."""
        idx = np.searchsorted(self.dist, lap_dist_pct)
        idx = int(np.clip(idx, 0, len(self.dist) - 1))
        return float(self.throttle[idx]), float(self.brake[idx])

    def slice(self, center: float, half_window: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (dist, throttle, brake) arrays for a window around center."""
        lo = center - half_window
        hi = center + half_window
        # Handle lap wrap-around
        if lo >= 0 and hi <= 1:
            mask = (self.dist >= lo) & (self.dist <= hi)
            return self.dist[mask], self.throttle[mask], self.brake[mask]
        # Wrap case: stitch end + beginning of lap
        if lo < 0:
            mask = (self.dist >= (1 + lo)) | (self.dist <= hi)
            d = np.concatenate([self.dist[self.dist >= (1 + lo)] - 1, self.dist[self.dist <= hi]])
            t = np.concatenate([self.throttle[self.dist >= (1 + lo)], self.throttle[self.dist <= hi]])
            b = np.concatenate([self.brake[self.dist >= (1 + lo)], self.brake[self.dist <= hi]])
            return d, t, b
        # hi > 1
        mask_end   = self.dist >= lo
        mask_start = self.dist <= (hi - 1)
        d = np.concatenate([self.dist[mask_end], self.dist[mask_start] + 1])
        t = np.concatenate([self.throttle[mask_end], self.throttle[mask_start]])
        b = np.concatenate([self.brake[mask_end], self.brake[mask_start]])
        return d, t, b
