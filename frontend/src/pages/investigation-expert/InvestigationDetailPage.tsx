import { useParams } from "react-router";
import SharedOpportunityDetail from "../../components/opportunity/SharedOpportunityDetail";
export default function InvestigationDetailPage(){const {opportunityId}=useParams();return opportunityId?<SharedOpportunityDetail opportunityId={opportunityId} role="INVESTIGATION_EXPERT"/>:null}
