class TemperamentoError(Exception):
    """Base class for all user-facing Temperamento errors."""


class MusicXMLError(TemperamentoError):
    """The input is not within the supported MusicXML subset."""


class HarmonyError(TemperamentoError):
    """A chord or harmonic relation cannot be decoded."""


class StaticError(TemperamentoError):
    """The score is syntactically valid MusicXML but invalid Temperamento."""


class RuntimeFault(TemperamentoError):
    """Execution cannot continue."""


class IntegrationError(TemperamentoError):
    """An external notation or rendering integration cannot complete."""
