# Base and core models first
from . import res_config_settings
from . import partner  # This should come before models that depend on it
# Then other models
from . import customer
from . import fleet_booking_status
from . import vehicle
from . import driver
from . import transport
from . import fleet_route
from . import fleet_route_stop
from . import fleet_booking  # This should come last as it depends on others
from . import fleet_vehicle_bridge