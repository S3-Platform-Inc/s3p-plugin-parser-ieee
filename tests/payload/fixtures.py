import pytest


# import signal
#
#
# def handler(signum, frame):
#     raise TimeoutError("Test took too long to execute")
#
#
# def execute_timeout(seconds):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             signal.signal(signal.SIGALRM, handler)
#             signal.alarm(seconds)
#             try:
#                 return func(*args, **kwargs)
#             finally:
#                 signal.alarm(0)  # Disable the alarm
#
#         return wrapper
#
#     return decorator

@pytest.fixture(scope="module")
def plugin_custom_params() -> dict:
    return {
        'url': 'https://ieeexplore.ieee.org/xpl/tocresult.jsp?isnumber=10005208&punumber=6287639&sortType=vol-only-newest',
        'categories': [
            "Computational and artificial intelligence",
            "Computers and information processing",
            "Communications technology",
            "Industry applications",
            "Vehicular and wireless technologies",
            "Systems engineering and theory",
            "Intelligent transportation systems",
            "Information theory",
            "Electronic design automation and methodology",
            "Education",
            "Social implications of technology"
        ]
    }
