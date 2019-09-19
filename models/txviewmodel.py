from iroha import IrohaCrypto
from proto.message import MessageModel


class TransactionViewModel:

  def __init__(self, model):
    self._model = model
    self.reset()

    self._direct_fields = [
        '.payload.reduced_payload.creator_account_id',
        '.payload.reduced_payload.created_time',
        '.payload.reduced_payload.quorum'
    ]

  @property
  def initialized(self):
    """
    Check whether the model is ready
    """
    return self._tx is not None

  def reset(self):
    """
    Clear internal state
    """
    self._tx = None
    self._mm = None

  def commit(self):
    """
    Commit current tx state to txs pool
    """
    if not self.initialized:
      return
    idx = self._model._current_tx_idx
    if idx is None:
      return
    self._model._txs_pool[idx] = self._tx

  def load(self):
    """
    Load current tx from txs pool
    """
    self.reset()
    idx = self._model._current_tx_idx
    if idx is None:
      return

    self._tx = self._model._txs_pool[idx]
    self._mm = MessageModel(self._tx)

  @property
  def data(self):
    if not self.initialized:
      return {}
    commands = []
    for i, cmd in enumerate(self._tx.payload.reduced_payload.commands):
      commands.append(('{} - {}'.format(i, cmd.DESCRIPTOR.name), i))
    data = {
        'batch_summary': self._batch_summary(),
        'commands_names': commands,
    }
    for field in self._direct_fields:
      data[field] = str(self._mm.read(field))

    return data

  @data.setter
  def data(self, value):
    if not self.initialized:
      return
    for k, v in value.items():
      if k in self._direct_fields:
        self._mm.set_to(k, v)

  def cleanup(self):
    idx = self._model._current_tx_idx
    if not self.initialized or idx is None:
      return
    if len(self._model._txs_pool[idx].payload.reduced_payload.creator_account_id) == 0:
      del self._model._txs_pool[idx]

  def _batch_summary(self):
    result = 'Non-batched transaction'
    if not self._tx.payload.HasField('batch'):
      return result
    batch_type = {
        0: 'ATOMIC',
        1: 'ORDERED'
    }[self._tx.payload.batch.type]
    count = len(self._tx.payload.batch.reduced_hashes)
    return '{} batch of {} transactions'.format(
        batch_type,
        count
    )
