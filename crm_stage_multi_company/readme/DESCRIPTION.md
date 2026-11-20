This module adds support for multi company on crm stage.

The new multi company rule prevents any user without access to all stages to open
the CRM application. This behaviour comes from the kanban view and especially from
he read_group (_read_group_fill_results) which tries to retrieve fold information
from the stages even those without any lead. So to only do this on accessible
stages a search is made by the current user over the stage ids returned by the
group_expand method which is initially launched through a sudo.

The stage of a lead is only chosen among the stages of the lead's company and the
stages without company, also when marking several leads of different companies as
won. When the company of a lead changes, a stage of another company is replaced by
the first stage of the new company, and the stage bar of the lead form only shows
the stages of the lead's company. On installation, the existing stages are assigned
to the current company, so leads without company (for example unassigned leads
created by the mail gateway) get no stage until stages without company are created.
