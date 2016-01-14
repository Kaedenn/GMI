#!/usr/bin/env python

class AssetProvider(object):
    def __init__(self, asset_def, equal_sizes=False):
        """AssetProvider(assets, equal_sizes=False)

        assets: a dict of asset names
        """
        self._assets = asset_def
