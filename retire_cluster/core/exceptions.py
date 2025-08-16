"""
Custom exceptions for Retire-Cluster
"""


class RetireClusterError(Exception):
    """Base exception for Retire-Cluster"""
    pass


class ConfigurationError(RetireClusterError):
    """Configuration related errors"""
    pass


class NetworkError(RetireClusterError):
    """Network communication errors"""
    pass


class DeviceError(RetireClusterError):
    """Device management errors"""
    pass


class RegistrationError(DeviceError):
    """Device registration errors"""
    pass


class HeartbeatError(DeviceError):
    """Heartbeat related errors"""
    pass


class TaskError(RetireClusterError):
    """Task execution errors"""
    pass


class DatabaseError(RetireClusterError):
    """Database operation errors"""
    pass