from data_elements.QuestionManager import QuestionRule, QuestionManager
from data_elements.VariableManager import VariableManager
from data_elements.Explanation import AffordanceBase, ClassExpression, ClassExpressionExplanation

# ====================== Rule ===================

push_rule = QuestionRule(property = "canPush",
                         rule = "Agent(?a), hasCapability(?a, ?c), PushingCapability(?c),\
                                 Object(?o), hasDisposition(?o, ?d), PushableDisposition(?d),\
                                 isApproachableBy(?o,?a), EndEffector(?g), hasComponent(?a,?g),\
                                 hasApplicableForce(?g,?w1), requiresForce(?o,?w2), equal(?w2,?w1)\
                                 -> canPush(?a, ?o)",
                          concepts = ['pushing', 'pushable', 'approachable', 'applicable_force', 'required_force', 'can push'])

# ====================== Variables ===================

variable_manager = VariableManager()
variable_manager.addClassVariable('__Object__',
                                  {'ToyWagon' : 'toy wagon',
                                   'RemoteControlledCar' : 'remote controlled car',
                                   'MiniShoppingCart' : 'shopping cart',
                                   'OfficeChair' : 'office chair',
                                   'RoombaRobot' : 'roomba'})

# ====================== Affordance ===================

affordance = AffordanceBase(capa=None, # Use the default capability
                            disp=None, # Use the default disposition
                            match=[
                                  "__gripper__|Type|Gripper",
                                  "Gripper|SubClassOf|EndEffector",
                                  "__agent__|hasComponent|__gripper__",
                                  "__gripper__|hasApplicableForce|integer#1",
                                  "__object__|requiresForce|integer#1",
                                  "equal(integer#1,integer#1)"
                                  ])

# =============== Disposition Explanation =============
disposition_expression = ClassExpression(easy= "PushableDisposition|EquivalentTo|(isDispositionOf some (hasPart some RollablePart))",
                                         medium= "PushableDisposition|EquivalentTo|(isDispositionOf some (hasPart some (RollablePart and (isOnRollableSurface value boolean#true)))",
                                         hard = "PushableDisposition|EquivalentTo|(isDispositionOf some (hasPart some (RollablePart and (isOnRollableSurface value boolean#true) and (isBlockedBySomething value boolean#false)))")

diposition_explanation = ClassExpressionExplanation(disposition_expression,
                                                    easy=["__object_disp__|isDispositionOf|__object__",
                                                          "__object__|hasPart|__wheel__",
                                                          "__wheel__|Type|__Wheel__",
                                                          "__Wheel__|SubClassOf|RollablePart"],
                                                    medium=["__wheel__|isOnRollableSurface|boolean#true"],
                                                    hard=["__wheel__|isBlockedBySomething|boolean#false"],
                                                    concatenate=True)

# =============== Capability Explanation =============
capability_expression = ClassExpression(easy= "PushingCapability|EquivalentTo|(isCapabilityOf some (hasGripper min 1 Gripper)",
                                        medium= "PushingCapability|EquivalentTo|(isCapabilityOf some (hasGripper min 1 (Gripper and (holdsSomething value boolean#false))",
                                        hard= "PushingCapability|EquivalentTo|(isCapabilityOf some (hasGripper min 1 (Gripper and (holdsSomething value boolean#false) and RigidEndEffector))")

capability_explanation = ClassExpressionExplanation(capability_expression,
                                                    easy=["__agent_capa__|isCapabilityOf|__agent__",
                                                          "__agent__|hasGripper|__gripper__",
                                                          "__gripper__|Type|__Gripper__",
                                                          "__Gripper__|SubClassOf|Gripper"],
                                                    medium=["__gripper__|holdsSomething|boolean#false"],
                                                    hard=["__gripper__|Type|RigidEndEffector"],
                                                    concatenate=True)

# =============== Property Explanation =============
property_expression = ClassExpression(easy = "", # chair isApproachableBy agent
                                      medium = "(isOnTable o isWithinMovingRangeOf)|SubPropertyOf|isApproachableBy", # box isOnTable table isWithinMovingRangeOf agent
                                      hard = "(isOnTable o isInSafeArea o isWithinMovingRangeOf)|SubPropertyOf|isApproachableBy") # box isOnTable table isInSafeArea __room__ isWithinMovingRangeOf agent

property_explanation = ClassExpressionExplanation(property_expression,
                                                  easy= ["__object__|isApproachableBy|__agent__"],
                                                  medium= [],
                                                  hard=[],
                                                  concatenate = True)

property_explanation.medium = ["__object__|isOnTable|__table__",
                               "__table__|isWithinMovingRangeOf|__agent__"]

property_explanation.hard = ["__object__|isOnTable|__table__",
                             "__table__|isInSafeArea|__room__",
                             "__room__|isWithinMovingRangeOf|__agent__"]

# =============== QuestionManager =============

push_manager = QuestionManager(push_rule,
                               variable_manager,
                               affordance,
                               capability_explanation,
                               diposition_explanation,
                               property_explanation)

#easy
# "concepts" : [
#   "can push", 
#   "pushable",
#   "pushing", 
#   "approachable", 
#   "applicable force", "required_force"  
# ]

# medium
# "concepts" : [
#   "can push", 
#   "pushable", "rollable_part_on_rollable_surface",
#   "pushing", "empty_hand",
#   "approachable", "object_on_table", "table_in_moving_range_robot",
#   "applicable force", "required_force"   
# ]

# hard
# "concepts" : [
#   "can push", 
#   "pushable", "rollable_part_on_rollable_surface", "rollable_part_unblocked",
#   "pushing", "empty_hand", "rigid",
#   "approachable", "object_on_table", "table_in_safe_area", "table_in_moving_range_robot",
#   "applicable force", "required_force"     
# ]

# gt_push_easy = "The __Agent__ can push the __Object__ because on one hand it has the pushing capability through having at least one gripper, \
#                 thanks to its __Gripper__. On the other hand, the __Object__ has the disposition of being pushable because it has some __Wheel__ which is a wheel. \
#                 Moreover the __Object__ is approachable by the __Agent__."
                
# gt_push_medium = "The __Agent__ can push the __Object__ because on one hand it has the pushing capability through having at least one gripper which\
#                 doesn't hold anything, thanks to its __Gripper__. On the other hand, the __Object__ has the disposition of being pushable because it has\
#                 some __Wheel__ which is a wheel and on a rollable surface. \
#                 Moreover the __Object__ is approachable by the __Agent__ because it is on a table that is within the moving range of the __Agent__."
                 
# gt_push_hard = "The __Agent__ can push the __Object__ because on one hand it has the pushing capability through having at least one gripper which \
#                   is also a rigid end effector and that doesn't hold anything, thanks to its __Gripper__. On the other hand, the __Object__ has the \
#                   disposition of being pushable because it has some __Wheel__ which is a wheel, on a rollable surface and unblocked. \
#                   Moreover the __Object__ is approachable by the __Agent__ because it is on a table that is in a safe area, which is within the moving range of the __Agent__."