from assetsy.processors import Processor

class Concat(Processor):
    def setup(self):
        from assetsy.assets import AssetSingle
        self.assetClass = AssetSingle
    def process_collection(self, assets):
        #output = args[0]
        asset = self.assetClass(environment = assets.environment,storage=assets.storage)
        flatten = assets.flatten
        asset.content = '\n'.join([_a.content for _a in flatten])
        asset.last_modified = max([_a.last_modified for _a in flatten])
        # asset.source = source
        return asset

# class Output (Processor):
#     def process_single(self,asset, output=lambda x:x.source):
#         outputfunc = (lambda x:asset.format_source(output)) if isinstance(output, basestring) else output
#         asset.output = outputfunc(asset)
#         return asset

class Versioner (Processor):
    def process_single(self,asset):
        asset.output['version'] = hash(asset)
        return asset