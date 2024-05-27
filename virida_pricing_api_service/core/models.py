import tensorflow as tf


class ConditionalFactorEncoder(tf.keras.Model):

    def __init__(self, inputs, units, seed=None, name='conditional_factor_encoder', **kwargs):
        # inputs: dict, name and shape of inputs
        # units: dict, {'input': int, input layer number of units,'hidden': list of int, hidden layers number of units}

        super().__init__(name=name, **kwargs)
        if seed:
            tf.random.set_seed(seed=seed)

        # Inputs
        self._inputs = {}
        for key in inputs:
            self._inputs[key] = tf.keras.layers.Dense(units=units['input'], activation='linear',
                                                      input_shape=(inputs[key],), name='input_layer_' + key,
                                                      dtype=tf.float32)

        # Layers
        self._layers = []
        for n in units['hidden']:
            self._layers = self._layers + [
                tf.keras.layers.Dense(units=n, activation='relu', name='hidden_layer_' + str(n), dtype=tf.float32)]

        # Output
        self._layers = self._layers + [
            tf.keras.layers.Dense(units=2, activation='linear', name='output_layer', dtype=tf.float32)]

    def __call__(self, inputs):
        # inputs: dict, numpy arrays, one-hot enconded conditions, prices and benchmark

        # Inputs
        x = []
        for key in self._inputs:
            x = x + [self._inputs[key](inputs[key])]
        x = tf.keras.layers.Concatenate()(x)

        # Network
        for layer in self._layers:
            x = layer(x)

        # Output
        beta, log_sigma = tf.split(x, [1, 1], axis=1)

        return {'beta': beta, 'log_sigma': log_sigma}


class ViridaPrices(tf.keras.Model):

    def __init__(self, inputs, units, outputs, seed=None, name='virida_prices', **kwargs):
        # inputs: dict (name and shape of inputs)
        # units: dict, {'input': int (input layer number of units),'hidden': list of int (hidden layers number of units)}
        # outputs: dict, {'beta': int (number of bechmarks),'sigma': int}

        super().__init__(name=name, **kwargs)
        if seed:
            tf.random.set_seed(seed=seed)

        # Inputs
        self._inputs = {}
        for key in inputs:
            self._inputs[key] = tf.keras.layers.Dense(units=units['input'],
                                                      activation='linear',
                                                      input_shape=(inputs[key],),
                                                      name='input_layer_' + key,
                                                      dtype=tf.float32)

        # Outputs
        n = []
        for key in outputs:
            n = n + [len(outputs[key])]
        self._outputs = dict(zip(list(outputs.keys()), n))

        # Layers
        self._layers = []
        for n in units['hidden']:
            self._layers = self._layers + [tf.keras.layers.Dense(units=n,
                                                                 activation='relu',
                                                                 name='hidden_layer_' + str(n),
                                                                 dtype=tf.float32)]

        n = sum(list(self._outputs.values()))
        self._layers = self._layers + [tf.keras.layers.Dense(units=n,
                                                             activation='linear',
                                                             name='output_layer',
                                                             dtype=tf.float32)]

    ###
    def __call__(self, inputs):
        # inputs: dict, numpy arrays, onehot enconded conditions, prices and benchmark

        # Inputs
        x = []
        for key in self._inputs:
            x = x + [self._inputs[key](inputs[key])]
        x = tf.keras.layers.Concatenate()(x)

        # Network
        for layer in self._layers:
            x = layer(x)

        # Outputs
        n = list(self._outputs.values())
        x = tf.exp(x)
        y = dict(zip(list(self._outputs.keys()), tf.split(x, n, axis=1)))

        return y


class Platts(tf.keras.Model):
  def __init__(self,inputs,units,outputs,seed=None,name='platts',**kwargs):
  # inputs: dict (name and shape of inputs)
  # units: dict, {'input': int (input layer number of units),'hidden': list of int (hidden layers number of units)}
  # outputs: dict, {'beta': int (number of bechmarks),'sigma': int}
    super().__init__(name=name,**kwargs)
    if seed:
      tf.random.set_seed(seed=seed)

    # Outputs
    n = []
    for key in outputs:
      n = n+[len(outputs[key])]
    self._outputs = dict(zip(list(outputs.keys()),n))
    # Layers
    self._layers = []
    for n in units['hidden']:
      self._layers = self._layers+[tf.keras.layers.Dense(units=n,activation='relu',name='hidden_layer_'+str(n),dtype=tf.float32)]
    n = sum(list(self._outputs.values()))
    self._layers = self._layers+[tf.keras.layers.Dense(units=n,activation='linear',name='output_layer',dtype=tf.float32)]
###
  def __call__(self,inputs):
  # inputs: dict, numpy arrays, onehot enconded conditions, prices and benchmark

    # Network
    x = inputs['index']
    for layer in self._layers:
      x = layer(x)
    # Outputs
    n = list(self._outputs.values())
    x = tf.exp(x)
    y = dict(zip(list(self._outputs.keys()),tf.split(x,n,axis=1)))
    return y
