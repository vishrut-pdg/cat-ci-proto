import { Navigate, Route, Routes } from "react-router";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute, RoleRoute } from "./auth/Routes";
import AppShell from "./components/layout/AppShell";
import LoginPage from "./pages/LoginPage";
import FinanceDashboard from "./pages/finance-analyst/FinanceDashboard";
import OpportunityShortlistingPage from "./pages/finance-analyst/OpportunityShortlistingPage";
import OpportunityDetailPage from "./pages/finance-analyst/OpportunityDetailPage";
import AssigningExpertPage from "./pages/finance-analyst/AssigningExpertPage";
import {CostSavingPage,LearningsPage,MonitorOutcomePage,RejectionPage} from "./pages/finance-analyst/PortfolioPages";
import ExpertDashboard from "./pages/investigation-expert/ExpertDashboard";
import MyInvestigationsPage from "./pages/investigation-expert/MyInvestigationsPage";
import InvestigationDetailPage from "./pages/investigation-expert/InvestigationDetailPage";

const Shell=({children}:{children:React.ReactNode})=><AppShell>{children}</AppShell>;
export default function App(){return <AuthProvider><Routes><Route path="/login" element={<LoginPage/>}/><Route element={<ProtectedRoute/>}><Route path="/" element={<Navigate to="/login" replace/>}/><Route element={<RoleRoute role="FINANCE_ANALYST"/>}><Route path="/finance-analyst" element={<Shell><FinanceDashboard/></Shell>}/><Route path="/finance-analyst/opportunity-shortlisting" element={<Shell><OpportunityShortlistingPage/></Shell>}/><Route path="/finance-analyst/assigning-an-expert" element={<Shell><AssigningExpertPage/></Shell>}/><Route path="/finance-analyst/monitor-outcome" element={<Shell><MonitorOutcomePage/></Shell>}/><Route path="/finance-analyst/opportunity-rejection" element={<Shell><RejectionPage/></Shell>}/><Route path="/finance-analyst/cost-saving" element={<Shell><CostSavingPage/></Shell>}/><Route path="/finance-analyst/monitor-learnings" element={<Shell><LearningsPage/></Shell>}/><Route path="/finance-analyst/opportunities/:opportunityId" element={<Shell><OpportunityDetailPage/></Shell>}/></Route><Route element={<RoleRoute role="INVESTIGATION_EXPERT"/>}><Route path="/investigation-expert" element={<Shell><ExpertDashboard/></Shell>}/><Route path="/investigation-expert/my-investigations" element={<Shell><MyInvestigationsPage/></Shell>}/><Route path="/investigation-expert/my-investigations/:opportunityId" element={<Shell><InvestigationDetailPage/></Shell>}/></Route></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes></AuthProvider>}
