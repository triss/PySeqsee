from farg.codelet import CodeletFamily
from apps.seqsee.anchored import SAnchored
from farg.exceptions import ConflictingGroupException
from apps.seqsee.subspaces.deal_with_conflicting_groups import SubspaceDealWithConflictingGroups

class CF_FocusOn(CodeletFamily):
  """Causes the required focusable to be added to the stream."""
  @classmethod
  def Run(cls, controller, focusable):
    controller.stream.FocusOn(focusable)

class CF_GroupFromRelation(CodeletFamily):
  """Causes the required relations' ends to create a group."""
  @classmethod
  def Run(cls, controller, relation):
    # If there is a group spanning the proposed group, perish the thought.
    left, right = relation.first.start_pos, relation.second.end_pos
    from apps.seqsee.util import GreaterThanEq, LessThanEq
    if tuple(controller.ws.GetGroupsWithSpan(LessThanEq(left), GreaterThanEq(right))):
      return
    anchored = SAnchored.Create(relation.first, relation.second,
                                underlying_mapping=relation.mapping)
    try:
      controller.ws.InsertGroup(anchored)
    except ConflictingGroupException as e:
      SubspaceDealWithConflictingGroups(
          controller,
          workspace_arguments=dict(new_group=anchored,
                                   incumbents=e.conflicting_groups))

class CF_DescribeAs(CodeletFamily):
  """Attempt to describe item as belonging to category."""
  @classmethod
  def Run(cls, controller, item, category):
    if not item.IsKnownAsInstanceOf(category):
      item.DescribeAs(category)

