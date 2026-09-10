"""List / switch Windows default audio output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Device:
    id: str
    name: str
    is_default: bool


def _is_render(device_id: str) -> bool:
    # WASAPI: 0.0.0.* = render (playback), 0.0.1.* = capture (mic)
    return "{0.0.0." in device_id


def _policy_config() -> Any:
    import comtypes
    from comtypes import GUID, HRESULT, COMMETHOD, CLSCTX_ALL, CoCreateInstance
    from ctypes import POINTER, c_int, c_long, c_void_p
    from ctypes.wintypes import LPCWSTR, BOOL

    class IPolicyConfig(comtypes.IUnknown):
        _case_insensitive_ = True
        _iid_ = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")
        _idlflags_ = []
        _methods_ = [
            COMMETHOD([], HRESULT, "GetMixFormat", (["in"], LPCWSTR, "pwstrId"), (["out"], POINTER(c_void_p), "ppFormat")),
            COMMETHOD([], HRESULT, "GetDeviceFormat", (["in"], LPCWSTR, "pwstrId"), (["in"], BOOL, "bDefault"), (["out"], POINTER(c_void_p), "ppFormat")),
            COMMETHOD([], HRESULT, "ResetDeviceFormat", (["in"], LPCWSTR, "pwstrId")),
            COMMETHOD([], HRESULT, "SetDeviceFormat", (["in"], LPCWSTR, "pwstrId"), (["in"], c_void_p, "pEndpointFormat"), (["in"], c_void_p, "pMixFormat")),
            COMMETHOD([], HRESULT, "GetProcessingPeriod", (["in"], LPCWSTR, "pwstrId"), (["in"], BOOL, "bDefault"), (["out"], POINTER(c_long), "pmftDefault"), (["out"], POINTER(c_long), "pmftMin")),
            COMMETHOD([], HRESULT, "SetProcessingPeriod", (["in"], LPCWSTR, "pwstrId"), (["in"], POINTER(c_long), "pmft")),
            COMMETHOD([], HRESULT, "GetShareMode", (["in"], LPCWSTR, "pwstrId"), (["out"], POINTER(c_void_p), "pMode")),
            COMMETHOD([], HRESULT, "SetShareMode", (["in"], LPCWSTR, "pwstrId"), (["in"], c_void_p, "pMode")),
            COMMETHOD([], HRESULT, "GetPropertyValue", (["in"], LPCWSTR, "pwstrId"), (["in"], c_void_p, "key"), (["out"], POINTER(c_void_p), "pv")),
            COMMETHOD([], HRESULT, "SetPropertyValue", (["in"], LPCWSTR, "pwstrId"), (["in"], c_void_p, "key"), (["in"], c_void_p, "pv")),
            COMMETHOD([], HRESULT, "SetDefaultEndpoint", (["in"], LPCWSTR, "pwstrId"), (["in"], c_int, "role")),
            COMMETHOD([], HRESULT, "SetEndpointVisibility", (["in"], LPCWSTR, "pwstrId"), (["in"], BOOL, "bVisible")),
        ]

    CLSID = GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}")
    return CoCreateInstance(CLSID, IPolicyConfig, CLSCTX_ALL)


def list_playback() -> list[Device]:
    from pycaw.constants import AudioDeviceState
    from pycaw.pycaw import AudioUtilities

    default_id = ""
    try:
        speakers = AudioUtilities.GetSpeakers()
        default_id = getattr(speakers, "id", None) or ""
        if not default_id and hasattr(speakers, "GetId"):
            default_id = speakers.GetId()
    except Exception:
        pass

    out: list[Device] = []
    for d in AudioUtilities.GetAllDevices():
        try:
            if d.state != AudioDeviceState.Active:
                continue
            did = d.id or ""
            if not _is_render(did):
                continue
            name = d.FriendlyName or did
            out.append(Device(id=did, name=name, is_default=(did == default_id)))
        except Exception:
            continue
    return out


def set_default(device_id: str) -> bool:
    try:
        policy = _policy_config()
        for role in (0, 1, 2):
            policy.SetDefaultEndpoint(device_id, role)
        return True
    except Exception:
        return False


def toggle_next() -> tuple[str | None, list[Device]]:
    devices = list_playback()
    if len(devices) < 2:
        return None, devices
    idx = next((i for i, d in enumerate(devices) if d.is_default), 0)
    nxt = devices[(idx + 1) % len(devices)]
    if not set_default(nxt.id):
        return None, devices
    return nxt.name, list_playback()
