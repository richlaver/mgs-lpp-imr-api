import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm


class instrument:
    def __init__(self, id) -> None:
        self.id = id
        self.project = None
        self.contract = None
        self.site = None
        self.zone = None
        self.short_id = None
        self.type = None
        self.subtype = None
        self.ground_level = None
        self.instrument_level = None
        self.sensor_depth = None
        self.location = None
        self.easting = None
        self.northing = None
        self.parents = None
        self.children = None
        self.date_installed = None
        self.parent_gr_level = None
        self.end_reading = None
        self.start_reading = None
        self.change = None
        self.max_in_period = None
        self.min_in_period = None
        self.is_imc = None
        self.imc_id = None
        self.imc_compare_reading = None
        self.end_imc_diff = None
        self.review_levels = None
        self.readings = None
        self.maxexceedance = None
        self.bearing = None


class MPLColorHelper:
  def __init__(self, cmap_name, start_val, stop_val):
    self.cmap_name = cmap_name
    self.cmap = plt.get_cmap(cmap_name)
    self.norm = mpl.colors.Normalize(vmin=start_val, vmax=stop_val)
    self.scalarMap = cm.ScalarMappable(norm=self.norm, cmap=self.cmap)

  def get_rgb(self, val):
    return self.scalarMap.to_rgba(val)