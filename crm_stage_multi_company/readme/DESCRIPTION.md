This module adds support for multi company on crm stage.

The new multi company rule prevents any user without access to all stages to open
the CRM application. This behaviour comes from the kanban view and especially from
he read_group (_read_group_fill_results) which tries to retrieve fold information
from the stages even those without any lead. So to only do this on accessible
stages a search is made by the current user over the stage ids returned by the
group_expand method which is initially launched through a sudo.
