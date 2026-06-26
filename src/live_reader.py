import irsdk


class LiveReader:
    """Polls iRacing shared memory for current telemetry values."""

    def __init__(self):
        self.ir = irsdk.IRSDK()
        self._connected = False

    def connect(self) -> bool:
        if not self._connected:
            self._connected = self.ir.startup()
        return self._connected

    def is_connected(self) -> bool:
        return self._connected and self.ir.is_connected

    def disconnect(self):
        self.ir.shutdown()
        self._connected = False

    def sample(self) -> dict | None:
        """Returns current telemetry dict or None if iRacing is not running."""
        if not self.is_connected():
            self.connect()
            return None

        self.ir.freeze_var_buffer_latest()
        try:
            return {
                'throttle':    self.ir['Throttle'],
                'brake':       self.ir['Brake'],
                'lap_dist_pct': self.ir['LapDistPct'],
                'on_track':    self.ir['IsOnTrack'],
            }
        except Exception:
            return None
