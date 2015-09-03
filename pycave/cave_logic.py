"""Tools for creating all "game" logic associated with a Cave project
"""
import warnings
try:
    import bpy
except ImportError:
    warnings.warn(
        "Module bpy not found. Loading pycave.cave_logic as standalone")

HEADER = """import bge
from time import monotonic"""


START_IMMEDIATELY = """
"""


BASE_FUNCTION = """
def activate_{cont_name}(cont):
    print("{cont_name}")
    scene = bge.logic.getCurrentScene()
    own = cont.owner
    sensor = cont.sensors["{cont_name}"]
    change_sensor = cont.sensors["{cont_name}_change"]
    property_actuator = cont.actuators["{cont_name}"]
    if {start_immediately}:
        root_sensor = cont.sensors["ROOT"]
        if root_sensor.positive:
            own["activation_time"] = monotonic()
            property_actuator.value = "True"
            print(own["{cont_name}"])
            cont.activate("{cont_name}")
            print(own["{cont_name}"])
    print("BASE")
    if change_sensor.positive and sensor.positive:
        own["activation_time"] = monotonic()
        property_actuator.value = "True"
        cont.activate("{cont_name}")
    if monotonic() - own["activation_time"] > {duration}:
        property_actuator.value = "False"
        cont.activate("{cont_name}")
"""

LINEAR_MOVEMENT = """
    actuator = cont.actuators["{actuator_name}"]
    target_position = {target_position}
    if change_sensor.positive and sensor.positive and {duration} != 0:
        for i in range(3):
            actuator.linV[i] = (target_position[i] -
                own.position[i])/{duration}
    if change_sensor.positive and sensor.negative:
        for i in range(3):
            actuator.linV[i] = 0
            actuator.Loc[i] = {target_position}[i]
    cont.activate("{actuator_name}")
"""


# Does a property changed through a python script properly register as changed
# to a property sensor?
ACTION_ACTIVATION = """
    print("ACTION_ACTIVATION")
    if (sensor.positive
            and not scene.objects["{target_object}"]["{controller_name}"]
            and own["activation_time"] >= {action_time}):
        scene.objects["{target_object}"].actuators[
            "{controller_name}"].value="True"
        cont.activate["{controller_name}"]
"""


def generate_object_control_script(object_name):
    """Generates initial script for Blender Python controller for this object

    :return Name of script
    """
    script_name = ".".join((object_name, "py"))
    #TODO: Set proper build directory
    with open(script_name, 'w') as control_file:
        control_file.write(HEADER)
    return script_name


def generate_project_root():
    """Generate a root object used to activate initial actions"""
    bpy.ops.object.add(
        type="EMPTY",
        layers=[layer == 20 for layer in range(1, 21)],
    )
    root_object = bpy.context.object
    bpy.context.scene.objects.active = root_object
    root_object.name = "ROOT"
    bpy.ops.logic.sensor_add(
        type="DELAY",
        object="ROOT",
        name="ROOT"
    )
    root_object.game.sensors[-1].name = "ROOT"
    root_object.game.sensors["ROOT"].delay = 0
    root_object.game.sensors["ROOT"].duration = 0
    root_object.game.sensors["ROOT"].use_repeat = False

    return root_object


def generate_python_controller(
        object_name, duration=0, start_immediately=False):
    """Generate a new Python controller for object

    This produces a Python controller with a unique name [controller_name]
    attached to two sensors and one actuator. Furthermore, it adds a property
    to the given object with the same name as that controller. One of the
    sensors, also named [controller_name], is activated when this property is
    True. The other sensor, named [controller_name]_change, is activated when
    the value of this property changes. When either of these sensors is
    activated, the controller is itself activated, doing all of the heavy
    lifting for an ObjectAction. When the controller is activated, it activates
    an actuator, also named [controller_name], which sets the [controller_name]
    property to either True or False. This allows the controller to turn itself
    off after a certain duration.

    :param str object_name: Name of object to which controller will be added
    :param float duration: Duration of action started by this controller
    :param bool start_immediately: Whether or not this action should start as
    soon as the Cave starts
    :return Name of new controller
    """
    blender_object = bpy.data.objects[object_name]
    bpy.context.scene.objects.active = blender_object
    controller_count = 0
    while True:
        controller_name = "_".join(
            (object_name, "controller", "{}".format(controller_count)))
        if controller_name not in blender_object.game.controllers:
            break
        controller_count += 1
    bpy.ops.logic.controller_add(
        type='PYTHON',
        object=object_name,
        name=controller_name)
    controller = blender_object.game.controllers[controller_name]
    controller.mode = "MODULE"
    controller.module = "{}.activate_{}".format(
        object_name, controller_name)

    # Property used to control when controller is triggered
    property_name = controller_name
    bpy.ops.object.game_property_new(
        type='BOOL',
        name=property_name
    )
    blender_object.game.properties[property_name].value = False
    # Actuator to change said property
    actuator_name = controller_name
    bpy.ops.logic.actuator_add(
        type="PROPERTY",
        object=object_name,
        name=actuator_name
    )
    blender_object.game.actuators[-1].name = actuator_name
    blender_object.game.actuators[actuator_name].property = property_name
    blender_object.game.actuators[actuator_name].value = "True"
    controller.link(actuator=blender_object.game.actuators[actuator_name])
    # Sensor to detect current property value
    sensor_name = controller_name
    bpy.ops.logic.sensor_add(
        type="PROPERTY",
        object=object_name,
        name=sensor_name
    )
    blender_object.game.sensors[-1].name = sensor_name
        # WARNING: For some reason, setting the name via sensor_add results in
        # distorted sensor names sometimes. The above line is a workaround
        # which guarantees that the sensor is properly named. Blender source
        # bug?
    blender_object.game.sensors[sensor_name].property = property_name
    blender_object.game.sensors[sensor_name].value = "True"
    controller.link(sensor=blender_object.game.sensors[sensor_name])
    # Sensor to detect when property has changed
    change_sensor_name = "_".join((controller_name, "change"))
    bpy.ops.logic.sensor_add(
        type="PROPERTY",
        object=object_name,
        name=change_sensor_name
    )
    blender_object.game.sensors[-1].name = change_sensor_name
    blender_object.game.sensors[change_sensor_name].property =\
        property_name
    blender_object.game.sensors[change_sensor_name].evaluation_type =\
        "PROPCHANGED"
    controller.link(sensor=blender_object.game.sensors[change_sensor_name])

    if start_immediately:
        link_to_root(object_name, controller_name)

    #TODO: Set proper build directory
    with open(".".join((object_name, "py")), 'a') as control_file:
        control_file.write(BASE_FUNCTION.format(
            cont_name=controller_name,
            duration=duration,
            start_immediately=start_immediately
            )
        )

    return controller_name


def link_to_root(object_name, controller_name):
    """Set action to start immediately when project runs

    Links action to root object, which will set the property associated with
    that controller to True"""
    blender_object = bpy.data.objects[object_name]
    root_object = bpy.data.objects["ROOT"]
    controller = blender_object.game.controllers[controller_name]
    controller.link(
        sensor=root_object.game.sensors["ROOT"])


def add_motion_logic(
        object_name, controller_name, target_position, duration):
    #TODO: Proper directory
    blender_object = bpy.data.objects[object_name]
    controller = blender_object.game.controllers[controller_name]
    controller_filename = ".".join((object_name, "py"))
    actuator_name = "_".join((object_name, "motion_actuator"))
    if actuator_name not in blender_object.game.actuators:
        bpy.ops.logic.actuator_add(
            type="MOTION",
            object=object_name,
            name=actuator_name
        )
    controller.link(
        actuator=blender_object.game.actuators[actuator_name])
    with open(controller_filename, "a") as controller_file:
        controller_file.write(LINEAR_MOVEMENT.format(
            actuator_name=actuator_name,
            target_position=target_position,
            duration=duration
            )
        )


def add_action_activation_logic(
        object_name, controller_name, target_object_name,
        target_controller_name, action_time=0):
    blender_object = bpy.data.objects[object_name]
    target_object = bpy.data.objects[target_object_name]
    controller = blender_object.game.controllers[controller_name]
    controller_filename = ".".join((object_name, "py"))
    controller.link(
        actuator=target_object.game.actuators[target_controller_name])
    with open(controller_filename, "a") as controller_file:
        controller_file.write(
            ACTION_ACTIVATION.format(
                target_object=target_object_name,
                controller_name=target_controller_name,
                action_time=action_time
            )
        )
