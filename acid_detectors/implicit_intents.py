from acid_detectors.utils import get_instruction_offset, track_method_call_action, should_analyze, track_string_value, \
    get_path_of_method, is_path_of_method_in_package


class IntentAnalysis(object):

    def __init__(self, action="NotTraceable"):
        if action == "":
            action = "NotTraceable"
        self.action = action


class ReceiverAnalysis(object):

    def __init__(self, filters):
        self.filters = filters

    def get_action(self):
        for f in self.filters:
            return f.action


class IntentFilterAnalysis(object):

    def __init__(self, action):
        self.action = action

#TODO improve variable tainting with XRefFrom and XRefTo
def get_implicit_intents(apk,d,dx,include_support=None):
    """
      Returns a list of Broadcast Intents that which action is set inside this method. They might not be declared in this method.
       The best moment to detect an intent is when its action is set.

      :rtype: Intent
    """
    intents = []
    instruction_paths = dx.tainted_packages.search_methods("Landroid/content/Intent;", "setAction", ".")
    instruction_paths.extend(dx.tainted_packages.search_methods("Landroid/content/Intent;", "<init>", "\(Ljava\/lang\/String"))
    for path in instruction_paths:
        src_class_name, src_method_name, src_descriptor =  path.get_src(d.get_class_manager())
        if should_analyze(src_class_name,include_support):
            method = d.get_method_by_idx(path.src_idx)
            i = method.get_instruction(0,path.idx)
            index = method.code.get_bc().off_to_pos(path.idx)
            intent = i.get_output().split(",")[1].strip()
            back_index = index
            while back_index > 0:
                back_index -= 1
                i2 = method.get_instruction(back_index)
                if intent in i2.get_output() and i2.get_op_value() in [0xC] :#12 is move-result-object
                    action = track_method_call_action(method,back_index,intent)
                    intent = IntentAnalysis(action.strip())
                    intents.append(intent)
                    back_index = -1
                if i2.get_op_value() == 0x1A and intent in i2.get_output(): #const-string
                    action = i2.get_output().split(",")[1].strip()
                    intent = IntentAnalysis(action[1:-1].strip())
                    intents.append(intent)
                    back_index = -1
    return intents


def get_not_exported_static_receivers(apk):
    receivers = []
    manifest = apk.get_AndroidManifest()
    receiver_list = manifest.getElementsByTagName('receiver')
    for receiver in receiver_list:
        if receiver.attributes.has_key("android:exported") and receiver.attributes.getNamedItem("android:exported").value == "false":
            action_list = receiver.getElementsByTagName('action')
            for action in action_list:
                values = action.attributes.values()
                for val in values:
                    if 'name' in val.name:
                        intentfilter = IntentFilterAnalysis(str(val.value))
                        filters = [intentfilter]
                        receiver = ReceiverAnalysis(filters)
                        receivers.append(receiver)
    activity_list = manifest.getElementsByTagName('activity')
    for activity in activity_list:
        if activity.attributes.has_key("android:exported") and activity.attributes.getNamedItem("android:exported").value == "false":
            action_list = activity.getElementsByTagName('action')
            for action in action_list:
                values = action.attributes.values()
                for val in values:
                    if 'name' in val.name:
                        intentfilter = IntentFilterAnalysis(str(val.value))
                        filters = [intentfilter]
                        receiver = ReceiverAnalysis(filters)
                        receivers.append(receiver)
    return receivers

def get_static_receivers(apk):
    receivers = []
    manifest = apk.get_AndroidManifest()
    receiver_list = manifest.getElementsByTagName('receiver')
    for receiver in receiver_list:
        if (receiver.attributes.has_key("android:exported") and receiver.attributes.getNamedItem("android:exported").value != "true") or not receiver.attributes.has_key("android:exported"):
            action_list = receiver.getElementsByTagName('action')
            for action in action_list:
                values = action.attributes.values()
                for val in values:
                    if 'name' in val.name:
                        intentfilter = IntentFilterAnalysis(str(val.value))
                        filters = [intentfilter]
                        receiver = ReceiverAnalysis(filters)
                        receivers.append(receiver)
    activity_list = manifest.getElementsByTagName('activity')
    for activity in activity_list:
        if (activity.attributes.has_key("android:exported") and activity.attributes.getNamedItem("android:exported").value != "true") or not activity.attributes.has_key("android:exported"):
            action_list = activity.getElementsByTagName('action')
            for action in action_list:
                values = action.attributes.values()
                for val in values:
                    if 'name' in val.name:
                        intentfilter = IntentFilterAnalysis(str(val.value))
                        filters = [intentfilter]
                        receiver = ReceiverAnalysis(filters)
                        receivers.append(receiver)
    return receivers

def get_dynamic_receivers(apk,d,dx,include_support=None):
    """
      Returns a list of all the Receivers registered inside a method

      :rtype: Receiver
    """
    receivers = []
    instruction_paths = dx.tainted_packages.search_methods(".", "registerReceiver", "\(Landroid\/content\/BroadcastReceiver")
    for path in instruction_paths:
        src_class_name, src_method_name, src_descriptor =  path.get_src(d.get_class_manager())
        if should_analyze(src_class_name,include_support):
            method = d.get_method_by_idx(path.src_idx)
            i = method.get_instruction(0,path.idx)
            index =  method.code.get_bc().off_to_pos(path.idx)
            if i.get_op_value() in [0x6E,0x6F,0x72]:#invoke-virtual { parameters }, methodtocall or invoke-super
                var = i.get_output().split(",")[2].strip() #The second argument holds the IntentFilter with the action
            elif i.get_op_value() == 0x74:#invoke-virtual/range {vx..vy},methodtocall
                var = i.get_output().split(",")[0].split(".")[-1]
            else:
                print "Error"
            action = track_intent_filter_direct(method,index-1,var)
            intentfilter = IntentFilterAnalysis(action)
            filters = []
            filters.append(intentfilter)
            receiver = ReceiverAnalysis(filters)
            receivers.append(receiver)
    return receivers

def track_intent_filter_direct(method,index,variable):
    """
        Tracks the value of the IntentFilter action
    :param method: is the method where we are searching
    :param index: is the next instruction after the declaration of the IntentFilter has been found
    :param variable: is the register name where the IntentFilter is placed
    :return:
    """
    action = "notDefinedInMethod"
    while index > 0:
        ins = method.get_instruction(index)
        if variable == ins.get_output().split(",")[0].strip() and "Landroid/content/IntentFilter;-><init>(Ljava/lang/String;" in ins.get_output():
            new_var = ins.get_output().split(",")[1].strip()
            action = track_string_value(method,index-1,new_var)
            return action
        elif (len(ins.get_output().split(",")) > 1 and variable == ins.get_output().split(",")[1].strip() and ins.get_op_value() in [0x07, 0x08]):#move-objects
            # Move operation, we just need to track the new variable now.
            new_var = ins.get_output().split(",")[0].strip()
            #print "++++"+new_var
            action2 = track_intent_filter_direct(method,index+1,new_var)
            if(action2 not in ["notDefinedInMethod", "registerReceiver"]):# it may happen that the same variable is referenced in two register. One leads to nowehere and the other is the correct one.
                action = action2
                return action
        elif (variable == ins.get_output().split(",")[0].strip() and "Landroid/content/IntentFilter;-><init>(Landroid/content/IntentFilter;" in ins.get_output()):
            # The intent filter is initialized with other intent filter.
            # We update the register name to look for.
            #TODO THIS GENERATES FALSE POSITIVES
            new_var = ins.get_output().split(",")[1].strip()
            action2 = track_intent_filter_direct(method,index+1,new_var)
            if(action2 not in ["notDefinedInMethod", "registerReceiver"]):# it may happen that the same variable is referenced in two register. One leads to nowehere and the other is the correct one.
                action = action2
                return action
        elif (variable == ins.get_output().split(",")[0].strip() and "addAction" in ins.get_output()):
            # There is an addAction that declares the action
            # We need to look for its value
            new_var = ins.get_output().split(",")[1].strip()
            if "p" in new_var:# the varaible comes from a method parameter
                action = "MethodParameter"
                return action
            else:
                action = track_string_value(method,index-1,new_var)
                return action
        elif (variable == ins.get_output().split(",")[0].strip() and ins.get_op_value() in [0x54]):#taking value from a method call.
            action = ins.get_output().split(",")[2].strip()
            return action
        elif "registerReceiver" in ins.get_output():
            action = "registerReceiverFoundWithouBeingAbleToTrackParameters"
            return action
        index -= 1
    return action