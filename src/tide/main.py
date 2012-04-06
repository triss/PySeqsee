"""The Main class is the entry point into an app.
"""
from third_party import gflags
from tide.controller import Controller
from tide.run_mode import batch, gui, single, sxs
from tide.ui.batch_ui import BatchUI
from tide.ui.gui import GUI
import logging
import sys

FLAGS = gflags.FLAGS

gflags.DEFINE_enum('run_mode', 'gui',
                   ('gui', 'batch', 'sxs', 'single'),
                   'Mode to run in. GUI creates a tkinter display, whereas batch and sxs '
                   'run the program multiple times non-interactively. Each such run uses '
                   'the "single" run mode.')
gflags.DEFINE_enum('debug', '', ('', 'debug', 'info', 'warn', 'error', 'fatal'),
                   'Show messages from what debug level and above?')
gflags.DEFINE_string('stopping_condition', None,
                     'Stopping condition, if any. Only allowed in non-gui modes. If the '
                     'condition is met, the program returns with a StoppingConditionMet '
                     'exception')

gflags.DEFINE_string('input_spec_file', None,
                     'Path specifying inputs over which to run batch processes.'
                     'This will be read by an instance of input_spec_reader_class.')
gflags.DEFINE_integer('num_iterations', 10,
                      "In batch and SxS mode, number of iterations to run", 1)
gflags.DEFINE_integer('max_steps', 1000,
                      "In batch and SxS mode, number of steps per run", 1)

class Main:
  #: Class to use for running in GUI mode.
  run_mode_gui_class = gui.RunModeGUI
  #: Class to use for running in Batch mode.
  run_mode_batch_class = batch.RunModeBatch
  #: Class to use for running in SxS mode.
  run_mode_sxs_class = sxs.RunModeSxS
  #: Class to use for running in single mode.
  run_mode_single_run_class = single.RunModeSingle

  #: GUI class to use for the tkinter GUI.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  gui_class = GUI
  #: Batch UI class to use for running in non-interactive mode. It should be able to handle
  #: any questions that may be generated by its codelets.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  batch_ui_class = BatchUI

  #: The controller runs the show by scheduling codelets to run.
  #: Subclasses of Main can override this, probably with a subclass of its value here.
  controller_class = Controller

  #: In batch and sxs modes, the inputs over which to run are specified in a file.
  #: These will be converted to flags passed to individual runs. An input reader should
  #: be specified for the file to series of flags conversion.
  #: These will usually be a subclass of ReadInputSpec.
  input_spec_reader_class = None

  #: A mapping between stopping condition names and their implmentation (which is a funtion
  #: that takes a controller and returns a bool).
  stopping_conditions = dict()


  def VerifyStoppingConditionSanity(self):
    """
    Make sure that stopping conditions are specified only in modes where they make sense.
    """
    run_mode_name = FLAGS.run_mode
    stopping_condition = FLAGS.stopping_condition
    if run_mode_name == 'gui':
      # There should be no stopping condition.
      if stopping_condition:
        raise ValueError("Stopping condition does not make sense with GUI.")
    else:  # Verify that the stopping condition's name is defined.
      if FLAGS.stopping_condition and FLAGS.stopping_condition != "None":
        if FLAGS.stopping_condition not in self.stopping_conditions:
          raise ValueError('Unknown stopping condition %s. Use one of %s' %
                           (FLAGS.stopping_condition, list(self.stopping_conditions.keys())))
        else:
          self.stopping_condition_fn = self.stopping_conditions[FLAGS.stopping_condition]
      else:
        self.stopping_condition_fn = ''

  def CreateRunModeInstance(self):
    """
    Create a Runmode instance from the flags.
    """
    run_mode_name = FLAGS.run_mode
    if run_mode_name == 'gui':
      return self.run_mode_gui_class(controller_class=self.controller_class,
                                     ui_class=self.gui_class)
    elif run_mode_name == 'single':
      return self.run_mode_single_run_class(controller_class=self.controller_class,
                                            ui_class=self.batch_ui_class,
                                            stopping_condition_fn=self.stopping_condition_fn)
    else:
      if not FLAGS.input_spec_file:
        error_msg = ('Runmode --run_mode=%s requires --input_spec_file to be specified' %
                     run_mode_name)
        raise ValueError(error_msg)
      input_spec = list(self.input_spec_reader_class().ReadFile(FLAGS.input_spec_file))
      print(input_spec)
      if run_mode_name == 'batch':
        return self.run_mode_batch_class(controller_class=self.controller_class,
                                         input_spec=input_spec)
      elif run_mode_name == 'sxs':
        return self.run_mode_sxs_class(controller_class=self.controller_class,
                                       input_spec=input_spec)
      else:
        raise ValueError("Unrecognized run_mode %s" % run_mode_name)

  def ProcessFlags(self):
    """Called after flags have been read in."""
    self.ProcessCustomFlags()

    self.VerifyStoppingConditionSanity()
    self.run_mode = self.CreateRunModeInstance()

    if FLAGS.debug:
      numeric_level = getattr(logging, FLAGS.debug.upper(), None)
      if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % FLAGS.debug)
      logging.basicConfig(level=numeric_level)

  def ProcessCustomFlags(self):
    """
    Apps can override this to process app-specific flags.
    """

  def Run(self):
    self.run_mode.Run()

  def main(self, argv):
    try:
      argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError as e:
      print('%s\nUsage: %s ARGS\n%s\n\n%s' % (e, sys.argv[0], FLAGS, e))
      sys.exit(1)

    self.ProcessFlags()
    self.Run()