class Ground:
    def __init__(self, outer):
        self.outer = outer
        self.matching_scene = self.find_matching_scene()
        self.dataset_metadata = self.get_metadata(self.matching_scene)
        self.found_layers = self.find_target_layers()
        self.raw_poi_data = self.extract_poi_data()
        self.poi_data = self.process_poi_data()
