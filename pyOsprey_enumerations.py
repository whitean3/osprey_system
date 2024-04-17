from enum import IntEnum, auto


# ========================================================================================================
# === ENUMERATIONS =======================================================================================

class OspreyEnums:

    class ConnectionMethod(IntEnum):
        """Connection method"""

        Ethernet = auto()
        USB = auto()

    class PresetType(IntEnum):
        """Preset type"""

        Continuous = auto()
        LiveTime = auto()
        RealTime = auto()

    class AutomaticManual(IntEnum):
        """Automatic or manual mode"""

        Automatic = 0
        Manual = 1
