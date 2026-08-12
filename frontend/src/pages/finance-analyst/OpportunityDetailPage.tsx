import { useParams } from "react-router";
import SharedOpportunityDetail from "../../components/opportunity/SharedOpportunityDetail";
export default function OpportunityDetailPage(){const {opportunityId}=useParams();return opportunityId?<SharedOpportunityDetail opportunityId={opportunityId} role="FINANCE_ANALYST"/>:null}
