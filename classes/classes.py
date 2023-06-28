import copy
import pandas as pd


class Activity:
    def __init__(self, ID, PROCESSING_TIME, PRODUCT, PRODUCT_ID, NEEDS):
        self.ID = ID
        self.PRODUCT = PRODUCT
        self.PRODUCT_ID = PRODUCT_ID
        self.PROCESSING_TIME = PROCESSING_TIME
        self.NEEDS = NEEDS
        self.SEQUENCE_ID = int()

    #TODO: Deepali will implement this function
    def sample_processing_Time(self, distribution_type="normal"):

        # This function can be used in different modes (for different distributions)
        if distribution_type == "normal":
            # Replace with sample step from stochastic distrbiution
            processing_time = 10

        elif distribution_type == "exponential":
            # Replace with sample step from stochastic distrbiution
            processing_time = 10

        elif distribution_type == "poisson":
            # Replace with sample step from stochastic distrbiution
            processing_time = 10

        # Distribution parameters should be stored in Activity object
        # Think of default parameters (mean, std.)
        return processing_time


class Product:
    def __init__(self, ID, NAME, ACTIVITIES=None, TEMPORAL_RELATIONS=None):
        self.ID = ID
        self.NAME = NAME
        self.DEADLINE = int()
        self._set_activities(ACTIVITIES)
        self._set_temporal_relations(TEMPORAL_RELATIONS)

    def add_activity(self, activity):
        """
        Add a product to the product
        :param product: Class Product
        """
        self.ACTIVITIES.append(activity)

    def set_temporal_relations(self, TEMPORAL_RELATIONS):
        # TODO currently self.PREDECESSORS not in use
        # TODO currently self.SUCCESSORS not in use
        self.TEMPORAL_RELATIONS = TEMPORAL_RELATIONS
        self.PREDECESSORS = [[] for _ in self.ACTIVITIES]
        self.SUCCESSORS = [[] for _ in self.ACTIVITIES]
        for (i, j) in self.TEMPORAL_RELATIONS.keys():
            self.PREDECESSORS[j].append(i)
            self.SUCCESSORS[i].append(j)

    def _set_activities(self, activities):
        activities_obj = []
        if activities:
            for activity in activities:
                if isinstance(activity, dict):
                    activities_obj.append(Activity(**activity))
                elif isinstance(activity, Activity):
                    activities_obj.append(activity)
                else:
                    raise TypeError("Invalid type of data provided needed: Activity or dict provided:", type(activity))

        self.ACTIVITIES = activities_obj

    def _set_temporal_relations(self, temporal_relations):

        TEMPORAL_RELATIONS = {}
        if (temporal_relations):
            for relation in temporal_relations:
                TEMPORAL_RELATIONS[(relation['SUCCESSOR'], relation['PREDECESSOR'])] = relation['REL']
        return TEMPORAL_RELATIONS


class Factory:
    def __init__(self, NAME, RESOURCE_NAMES, CAPACITY, PRODUCTS=None):
        self.NAME = NAME
        self._set_products(PRODUCTS)
        self.RESOURCE_NAMES = RESOURCE_NAMES
        self.CAPACITY = CAPACITY

    def add_product(self, product):
        """
        Add a product to the production plan
        :param product: Class Product
        """
        self.PRODUCTS.append(product)

    def _set_products(self, products):
        products_obj = []
        if products:
            for product in products:
                if isinstance(product, dict):
                    products_obj.append(Product(**product))
                elif isinstance(product, Product):
                    products_obj.append(product)
                else:
                    raise TypeError("Invalid type of data provided needed: Product or dict provided:", type(product))

        self.PRODUCTS = products_obj


class ProductionPlan:
    def __init__(self, ID, SIZE, NAME, FACTORY, PRODUCT_IDS, DEADLINES):
        self.ID = ID
        self.SIZE = SIZE
        self.NAME = NAME
        self.FACTORY = FACTORY
        self.PRODUCT_IDS = PRODUCT_IDS
        self.DEADLINES = DEADLINES
        self.SEQUENCE = []
        self.PRODUCTS = []

    def list_products(self):
        """
        Add a product to the production plan
        :param product: Class Product
        """
        self.PRODUCTS = []
        for i in range(0, len(self.PRODUCT_IDS)):
            product = copy.copy(self.FACTORY.PRODUCTS[self.PRODUCT_IDS[i]])
            product.DEADLINE = self.DEADLINES[i]
            self.PRODUCTS.append(product)
        self.SIZE = len(self.PRODUCT_IDS)

    def set_sequence(self, sequence):
        """
        Give the sequence in which the products will be processed
        :param sequence: list of integers
        """
        self.SEQUENCE = sequence

    def convert_to_dataframe(self):
        df = pd.DataFrame()
        df["Product_ID"] = self.PRODUCT_IDS
        df["Deadlines"] = self.DEADLINES
        return df

    def set_earliest_start_times(self, earliest_start):
        self.earliest_start = earliest_start

