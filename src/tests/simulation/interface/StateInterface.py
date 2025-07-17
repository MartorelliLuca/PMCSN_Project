from datetime import datetime
class StateInterface:

    def get_block_name(self)->str:
        pass

    def queue_length(self)->int:
        pass

    def get_queue_enter_time(self)->datetime:
        pass

    def get_queue_exit_time(self)->datetime:
        pass

    def get_working_end(self)->datetime:
        pass    

    def get_next_event_time(self)->datetime:
        pass   