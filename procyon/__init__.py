# vim: ts=4 sts=4 et sw=4

# Don't forget to updte the import whenever __all__ is modified!
from .interpreter import evaluate, evaluate_command, evaluate_file
__all__ = ['evaluate', 'evaluate_command', 'evaluate_file']
