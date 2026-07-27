"""Optimizer service for email marketing optimization."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import ApprovalStatus, Proposal
from app.models.campaign import Campaign, CampaignStatus
from app.services.analytics import get_account_metrics, get_campaign_metrics


async def generate_optimization_proposals(
    session: AsyncSession,
) -> List[Proposal]:
    """Generate optimization proposals based on campaign performance.

    Args:
        session: Database session

    Returns:
        List of optimization proposals
    """
    proposals = []

    # Get recent campaigns
    week_ago = datetime.utcnow() - timedelta(days=7)

    result = await session.execute(
        select(Campaign).where(
            Campaign.status == CampaignStatus.RUNNING,
            Campaign.created_at >= week_ago,
        )
    )
    campaigns = list(result.scalars().all())

    for campaign in campaigns:
        # Get campaign metrics
        metrics = await get_campaign_metrics(session, str(campaign.id))

        # Check for low open rate
        if metrics.get("open_rate", 0) < 10:
            proposals.append(
                Proposal(
                    title="Low Open Rate",
                    rationale=f"Campaign '{campaign.name}' has a low open rate of {metrics.get('open_rate', 0)}%",
                    changes={
                        "suggested_action": "Consider changing the subject line or send time"
                    },
                    status=ApprovalStatus.PENDING,
                )
            )

        # Check for low click rate
        if metrics.get("click_rate", 0) < 2:
            proposals.append(
                Proposal(
                    title="Low Click Rate",
                    rationale=f"Campaign '{campaign.name}' has a low click rate of {metrics.get('click_rate', 0)}%",
                    changes={
                        "suggested_action": "Consider adding more compelling CTAs or improving content"
                    },
                    status=ApprovalStatus.PENDING,
                )
            )

        # Check for high bounce rate
        if metrics.get("bounce_rate", 0) > 5:
            proposals.append(
                Proposal(
                    title="High Bounce Rate",
                    rationale=f"Campaign '{campaign.name}' has a high bounce rate of {metrics.get('bounce_rate', 0)}%",
                    changes={"suggested_action": "Consider cleaning your contact list"},
                    status=ApprovalStatus.PENDING,
                )
            )

    # Get account-wide metrics
    account_metrics = await get_account_metrics(session)

    # Check overall delivery rate
    if account_metrics.get("delivery_rate", 0) < 90:
        proposals.append(
            Proposal(
                title="Low Overall Delivery Rate",
                rationale=f"Account delivery rate is {account_metrics.get('delivery_rate', 0)}%",
                changes={
                    "suggested_action": "Consider cleaning your contact list and reviewing suppression rules"
                },
                status=ApprovalStatus.PENDING,
            )
        )

    # Check complaint rate
    if account_metrics.get("complaint_rate", 0) > 0.1:
        proposals.append(
            Proposal(
                title="High Complaint Rate",
                rationale=f"Account complaint rate is {account_metrics.get('complaint_rate', 0)}%",
                changes={
                    "suggested_action": "Review your email content and sending practices"
                },
                status=ApprovalStatus.PENDING,
            )
        )

    # Save proposals
    for proposal in proposals:
        session.add(proposal)

    await session.commit()
    return proposals


async def get_optimization_recommendations(
    session: AsyncSession,
    campaign_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get optimization recommendations for a campaign or account.

    Args:
        session: Database session
        campaign_id: Optional campaign ID

    Returns:
        List of recommendations
    """
    recommendations = []

    if campaign_id:
        # Get campaign metrics
        metrics = await get_campaign_metrics(session, campaign_id)

        if metrics.get("open_rate", 0) < 15:
            recommendations.append(
                {
                    "type": "subject_line",
                    "title": "Subject Line Optimization",
                    "description": "Your open rate is below 15%. Consider A/B testing different subject lines.",
                    "suggested_actions": [
                        "Try shorter subject lines (under 50 characters)",
                        "Use personalization tokens",
                        "Create urgency or curiosity",
                    ],
                    "priority": "high",
                }
            )

        if metrics.get("click_rate", 0) < 3:
            recommendations.append(
                {
                    "type": "content",
                    "title": "Content Optimization",
                    "description": "Your click rate is below 3%. Consider improving your email content.",
                    "suggested_actions": [
                        "Add more clear CTAs",
                        "Improve email layout and readability",
                        "Use more engaging visuals",
                    ],
                    "priority": "medium",
                }
            )

        if metrics.get("bounce_rate", 0) > 3:
            recommendations.append(
                {
                    "type": "list_cleaning",
                    "title": "List Cleaning",
                    "description": "Your bounce rate is above 3%. Consider cleaning your contact list.",
                    "suggested_actions": [
                        "Remove invalid email addresses",
                        "Re-engage inactive contacts",
                        "Review your signup forms",
                    ],
                    "priority": "high",
                }
            )
    else:
        # Account-wide recommendations
        account_metrics = await get_account_metrics(session)

        if account_metrics.get("delivery_rate", 0) < 95:
            recommendations.append(
                {
                    "type": "delivery_rate",
                    "title": "Improve Delivery Rate",
                    "description": "Your overall delivery rate is below 95%.",
                    "suggested_actions": [
                        "Clean your contact list",
                        "Review your sending frequency",
                        "Check your domain authentication",
                    ],
                    "priority": "high",
                }
            )

        if account_metrics.get("complaint_rate", 0) > 0.1:
            recommendations.append(
                {
                    "type": "complaint_rate",
                    "title": "Reduce Complaints",
                    "description": "Your complaint rate is above 0.1%.",
                    "suggested_actions": [
                        "Review your email content",
                        "Check your sending frequency",
                        "Ensure proper unsubscribe links",
                    ],
                    "priority": "critical",
                }
            )

    return recommendations


async def run_weekly_optimizer(
    session: AsyncSession,
) -> Dict[str, Any]:
    """Run the weekly optimizer run.

    Args:
        session: Database session

    Returns:
        Summary of optimization results
    """
    # Generate proposals
    proposals = await generate_optimization_proposals(session)

    # Get recommendations
    recommendations = await get_optimization_recommendations(session)

    # Get account metrics
    account_metrics = await get_account_metrics(session)

    return {
        "generated_proposals": len(proposals),
        "high_priority_proposals": sum(1 for p in proposals if p.priority == "high"),
        "critical_proposals": sum(1 for p in proposals if p.priority == "critical"),
        "recommendations": recommendations,
        "account_metrics": account_metrics,
        "generated_at": datetime.utcnow().isoformat(),
    }


async def apply_proposal(
    session: AsyncSession,
    proposal_id: str,
    apply: bool = True,
) -> bool:
    """Apply or reject an optimization proposal.

    Args:
        session: Database session
        proposal_id: Proposal ID
        apply: Whether to apply the proposal

    Returns:
        True if successful
    """
    result = await session.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()

    if not proposal:
        return False

    if apply:
        proposal.status = ApprovalStatus.APPROVED
    else:
        proposal.status = ApprovalStatus.REJECTED

    await session.commit()
    return True
