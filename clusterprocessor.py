'''
Provide a class that can do cluster file processing.  
This is done as follows:

1. The specified file is sucked in and the existence of all files
is validated (and assumed to be available to the server).
2. Each file is set as a data source and data processing starts.
3. A QTimer is sused to monitor file processing completion.
and used to start the next file.

'''

from os import path

from PyQt5.QtCore import pyqtSignal, QTimer



class ClusterProcessor(QTimer):
    '''
    Cluster file processor.
      Signals:
         done - cluster file processing is done.
         processing - started processing an event file (name is parameterized).
    '''
    done = pyqtSignal()
    processing = pyqtSignal(str)
    def __init__(self, cluster_file, poll, client, *args):
        super().__init__(*args)
    
        self._client = client
        self._poll = poll
        self._state = 'active'   # Becomes done when done.
        
        # Connect the timer to the poller:
        
        self.timeout.connect(self._poll_active)
    
        # Get the event files from file and test their
        # existence:
        
    
        self.event_files = []
        with open(cluster_file, "r") as file:
            for line in file:
                # Check existence:
                
                if not path.isFile(line):
                    self._state = 'done'
                    raise SystemError(f'No such event file {line} in cluster file {cluster_file}')
                
                #  Add to the list
                self._event_files.append(line)
        if len(self._event_files) > 0:
            self._current_file = self._event_files.pop(0)
            self._start_event_file(self._current_file)
                
    def abort(self):
        self._state = 'aborting'
           
    def _start_event_file(self, name):
        # Start prodessing an event file
        # The client is used to attach the file and
        # start processing.
        # We then start polling for done with the _poll_active metdhod.
        
        self._client.attach_source('file', name)
        self._client.start_analysis()
        self.processing.emit(name)
        self.start(self._poll)
        
    
    def _poll_active(self):
        #  Periodic poll:
        #   If state = 'aborting' set the state to 'done' emit the done signal.
        #   Otherwise, check the RunState Variable:
        #   If "Active" then just reschedule and leave state along.
        #   IF "Inactive" start the next event file if there is one and
        #    if not, emit the done stignal and set the state to done.
        
        if self._state == 'aborting':
            # Abort was requested.
            self._state = 'done'
            self.done.emit()
            return
        
        vars = client.shmem_getvariables()
        if vars['RunState'] == 'Inactive':
            # Finished a file:
            
            if len(self.event_files) == 0:
                self._state = 'done'
                self.done.emit()
            else:
                # Start the next file:
                next_file = self._eventfiles.pop(0)
                self._start_event_file(next_file)
        else:
            self.start(self._poll)