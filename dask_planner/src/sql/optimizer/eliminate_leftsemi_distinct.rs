use datafusion_common::Result;
use datafusion_expr::{
    logical_plan::{JoinType, LogicalPlan},
    utils::from_plan,
};
use datafusion_optimizer::{utils, OptimizerConfig, OptimizerRule};

#[derive(Default)]
pub struct EliminateLeftSemiDistinct {}

impl EliminateLeftSemiDistinct {
    #[allow(missing_docs)]
    pub fn new() -> Self {
        Self {}
    }
}

impl OptimizerRule for EliminateLeftSemiDistinct {
    fn optimize(
        &self,
        plan: &LogicalPlan,
        optimizer_config: &mut OptimizerConfig,
    ) -> Result<LogicalPlan> {
        // optimize inputs first
        // let plan = utils::optimize_children(self, plan, optimizer_config)?;

        match plan {
            LogicalPlan::Join(join) if (join.join_type == JoinType::LeftSemi) => {
                match join.left.as_ref() {
                    LogicalPlan::Distinct(distinct) => {
                        let left =
                            utils::optimize_children(self, &distinct.input, optimizer_config)?;
                        let right = utils::optimize_children(self, &join.right, optimizer_config)?;
                        let new_plan = from_plan(plan, &plan.expressions(), &[left, right])?;
                        Ok(new_plan)
                    }
                    _ => utils::optimize_children(self, plan, optimizer_config),
                }
            }
            _ => utils::optimize_children(self, plan, optimizer_config),
        }
    }

    fn name(&self) -> &str {
        "eliminate_leftsemi_distinct"
    }
}
